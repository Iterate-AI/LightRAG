from qdrant import Qdrant
from config.configure_env import ENV_CONFIG
from utils.ds_py_models import gpt4o
import dspy
from services.langfuse_client import langfuse
from fastembed.sparse.bm25 import Bm25
from services.format_enforcers import element_file_format_enforcer
from bs4 import BeautifulSoup
from utils.backend import handle_error
from utils.logger import logger
bm25_embedding_model = Bm25("Qdrant/bm25")

qdrant_client = Qdrant(ENV_CONFIG["QDRANT_URL"], ENV_CONFIG["QDRANT_API_KEY"], ENV_CONFIG["INFERLESS_TOKEN"])


def extract_react_attributes(html_snippet):
    """
    Extracts attributes from an HTML element relevant to React code and returns them as a dictionary.

    Args:
        html_snippet (str): A string containing the HTML snippet.

    Returns:
        dict: A dictionary containing the element's attributes and text content.
    """
    # Parse the HTML snippet
    soup = BeautifulSoup(html_snippet, "html.parser")

    # Find the first HTML element in the snippet
    element = soup.find()

    # Check if an element was found
    if not element:
        return {}

    # Initialize the output dictionary
    output = {}

    # Attributes to include (relevant to React code)
    INCLUDED_ATTRIBUTES = ["id", "class", "href", "src", "title", "alt", "name", "value", "type", "placeholder", "data-", "aria-"]

    # Get the attributes of the element
    attrs = element.attrs

    # Iterate over the attributes
    for attr, value in attrs.items():
        # Map 'class' to 'classname'
        if attr == "class":
            # Join class list into a space-separated string
            output["classname"] = " ".join(value) if isinstance(value, list) else value
        elif any(attr.startswith(prefix) for prefix in INCLUDED_ATTRIBUTES):
            output[attr] = value

    # Include the tag name
    output["tag"] = element.name

    # Include the text content, stripped of leading/trailing whitespace
    text_content = element.get_text(strip=True)
    if text_content:
        output["text"] = text_content

    return output


class query_reformulator(dspy.Signature):
    """
    Analyze an HTML or React snippet and generate a search query that captures its essential structure and meaning.

    Args:
        HTML_properties (dict): Processed HTML snippet containing key information relevant to React code.
        HTML (str): The original HTML snippet.
        previous_query (str): The previous query that didn't yield results (empty string if first attempt).

    Returns:
        str: A search query that preserves the essential structure and meaning of the original content.

    This function focuses on:
    1. Preserving key elements shared between HTML and React:
       - Anchor tags
       - Class names (used for styling)
       - href attributes (or 'to' in React Router)
       - Text content
    2. Retaining these features exactly as they appear in the original snippet.
    3. Removing elements not typically visible in React code (e.g., underlying CSS details).
    4. Generating a query that maintains both the structure and meaning of the original content.
    5. Remove any words that are not to be searched for, do not output readable english but a query containing only the words whose occurance is relevant to the search.
    6. given href="/abc/bcd/def" break it down into href="/abc/bcd/def" href="/abc/bcd" href="/abc"
    7. If a previous query is provided, adjust the new query to be different and potentially more effective. break down the href if possible also try removing the classname if the previous query has it.
    """

    HTML_properties = dspy.InputField()
    HTML = dspy.InputField()
    previous_query = dspy.InputField()
    query = dspy.OutputField()
    # code_query = dspy.OutputField()


def reformulate_query(HTML_properties, HTML, previous_query=""):
    reformulate = dspy.Predict(query_reformulator)
    with dspy.context(lm=gpt4o):
        pred = reformulate(HTML_properties=HTML_properties, HTML=HTML, previous_query=previous_query)
        if langfuse:
            gpt4o.tracker_call(tracker=langfuse)

    return pred.query, pred.query


class element_file_finder(dspy.Signature):
    """
        You are working with a React codebase and need to identify which part of the code (component or file) is responsible for rendering a given HTML structure.

    You are provided with:

    React code snippets: Each snippet is paired with its file path (e.g., client/src/pages/SignIn.jsx), representing parts of the rendering logic.
    HTML structure: The rendered HTML you want to trace back to its source in the React code.
    Input
    Code snippets: A list of objects with:

    filepath: The location of the React file.
    snippet: A chunk of React code (JSX, hooks, logic).
    HTML structure: The rendered HTML to match.

    Output
    Identify the React code responsible for rendering the provided HTML and its filepath. Your analysis should:

    Determine which JSX, JS, TS, TSX structure corresponds to the HTML. then output the filepath and reason.

    In case none of the snippets look like they are the source of the html then output {"filepath": "None", "reason": "None"}
    """

    HTML = dspy.InputField()
    context = dspy.InputField()
    filepath = dspy.OutputField(
        desc="""{"filepath": "some filepath", "reason": "reason why this is the filepath of the element which rendered the HTML"}"""
    )
    # code_query = dspy.OutputField()


def find_element_file(HTML, context):
    file_finder = dspy.ChainOfThought(element_file_finder)
    with dspy.context(lm=gpt4o):
        pred = file_finder(HTML=HTML, context=context)
        if langfuse:
            gpt4o.tracker_call(tracker=langfuse)

    return pred.filepath

async def find_element_path(collection, HTML, base_url, message_id, retries=5):
    previous_query = ""
    try:
        for attempt in range(retries):
            text_query, code_query = reformulate_query(str(extract_react_attributes(HTML)), HTML, previous_query)
            print(f"Attempt {attempt + 1} - text_query: {text_query}")

            # Convert text query to vector using Inferless
            text_query_vector = qdrant_client.embeddings.encode_text(shape=1, texts=[text_query])["outputs"][0]["data"]

            # Convert code query to vector using Inferless
            code_query_vector = qdrant_client.embeddings.encode_code(shape=1, codes=[code_query])["outputs"][0]["data"]

            text_query_sparse_vector = next(bm25_embedding_model.query_embed(text_query))
            code_query_sparse_vector = next(bm25_embedding_model.query_embed(code_query))

            text_points = qdrant_client.hybrid_search_points_text(collection, text_query_vector, text_query_sparse_vector)
            code_points = qdrant_client.hybrid_search_points_code(collection, code_query_vector, code_query_sparse_vector)

            results = []

            def process_points(points):
                for point in points:
                    if hasattr(point, "payload") and "context" in point.payload:
                        filepath = point.payload["context"].get("file_path", "N/A")
                        snippet = point.payload["context"].get("snippet", "N/A")
                        results.append({"filepath": filepath, "snippet": snippet})

            process_points(text_points.points)
            process_points(code_points.points)

            # Convert results to string and print its character length
            results_string = str(results)
            print(f"Character length of results: {len(results_string)}")

            filepath_and_reason = element_file_format_enforcer(find_element_file(HTML, results_string))

            print("###########################")
            print("filepath", filepath_and_reason)
            print("###########################")

            if filepath_and_reason["filepath"].lower() != "none":
                return filepath_and_reason["filepath"]

            previous_query = text_query

        print(f"No matching filepath found after {retries} attempts.")
        if filepath_and_reason["filepath"].lower() == "none":
            return None
        return None

    except Exception as e:
        logger.error("element_filepath", extra={"message": str(e)})
        print("element_filepath", e, flush=True)
        error_payload, _ = handle_error(
            base_url,
            message_id,
            "ELEMENT_FILEPATH_ERROR",
            e,
            "Error finding element filepath"
        )
        raise Exception(error_payload["error_message"])

