import os
from lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete, gpt_4o_complete
import time
import json
from openai import OpenAI
#########
# Uncomment the below two lines if running in a jupyter notebook to handle the async nature of rag.insert()
# import nest_asyncio
# nest_asyncio.apply()
#########

WORKING_DIR = "./outputs/local_excalidraw_split_by_file_lean"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=gpt_4o_mini_complete,  # Use gpt_4o_mini_complete LLM model
    # llm_model_func=gpt_4o_complete  # Optionally, use a stronger model
)

start_time = time.time()
with open("./code_excalidraw_split_by_file.txt", "r", encoding="utf-8") as f:
    rag.insert(f.read())
end_time = time.time()
print(f"Time taken: {end_time - start_time:.2f} seconds")

# print(rag.query("""What part of the code renders this html <div class="ToolIcon__icon"><svg aria-hidden="true" focusable="false" role="img" viewBox="0 0 20 20" class="" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><g stroke-width="1.25"></g></svg><span class="ToolIcon__keybinding">9</span></div>""", param=QueryParam(
#     mode="mix"))) #click on tool icon

# print(rag.query("""What part of the code contains the react component that renders this html \"<select><option value=\\\"en\\\">English</option><option value=\\\"id-ID\\\">Bahasa Indonesia</option><option value=\\\"de-DE\\\">Deutsch</option><option value=\\\"es-ES\\\">Espa\u00f1ol</option><option value=\\\"eu-ES\\\">Euskara</option><option value=\\\"fr-FR\\\">Fran\u00e7ais</option><option value=\\\"gl-ES\\\">Galego</option><option value=\\\"it-IT\\\">Italiano</option><option value=\\\"ku-TR\\\">Kurd\u00ee</option><option value=\\\"nb-NO\\\">Norsk bokm\u00e5l</option><option value=\\\"oc-FR\\\">Occitan</option><option value=\\\"pl-PL\\\">Polski</option><option value=\\\"pt-BR\\\">Portugu\u00eas Brasileiro</option><option value=\\\"ro-RO\\\">Rom\u00e2n\u0103</option><option value=\\\"sk-SK\\\">Sloven\u010dina</option><option value=\\\"sl-SI\\\">Sloven\u0161\u010dina</option><option value=\\\"sv-SE\\\">Svenska</option><option value=\\\"tr-TR\\\">T\u00fcrk\u00e7e</option><option value=\\\"cs-CZ\\\">\u010cesky</option><option value=\\\"ru-RU\\\">\u0420\u0443\u0441\u0441\u043a\u0438\u0439</option><option value=\\\"uk-UA\\\">\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430</option><option value=\\\"ar-SA\\\">\u0627\u0644\u0639\u0631\u0628\u064a\u0629</option><option value=\\\"mr-IN\\\">\u092e\u0930\u093e\u0920\u0940</option><option value=\\\"ja-JP\\\">\u65e5\u672c\u8a9e</option><option value=\\\"zh-CN\\\">\u7b80\u4f53\u4e2d\u6587</option><option value=\\\"zh-TW\\\">\u7e41\u9ad4\u4e2d\u6587</option><option value=\\\"ko-KR\\\">\ud55c\uad6d\uc5b4</option></select>\"""", param=QueryParam(
#     mode="mix"))) # open menu
def generate_query(target_html, target_context_html):
    """
    Generate query for webpage interaction analysis using target HTML and context HTML.
    
    Args:
        target_html: HTML of the target element
        target_context_html: Surrounding HTML context
        
    Returns:
        Query string for searching the codebase
    """
    # Initialize OpenAI client
    client = OpenAI(api_key="OPENAI_API_KEY")
    
    # Construct detailed prompt
    prompt = f"""Analyze this webpage interaction:

ELEMENT STRUCTURE:
1. Target Element HTML:
{target_html}

2. Surrounding Context HTML:
{target_context_html}

Based on this information, please:
1. Analyze the interaction and its context
2. Identify key characteristics of the interacted element
3. Explain the likely purpose and functionality
4. Suggest React component patterns or code structures that might be responsible
5. Provide search terms or patterns to locate this component in a React codebase

Focus on technical details that would help locate the source code, such as:
- Distinctive class names or patterns
- Component hierarchy hints
- Common React patterns for this type of interaction
- Potential file locations based on functionality
- Ask to output the filepath of the component
Please analyze this interaction and provide a JSON response in the format:
{{
    'query': 'what is the filepath of the element  of the description - An elaborate search query that captures the key characteristics and functionality of this component for hybrid vector database search'
}}"""

    # Make the API call
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1000,
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    response_json = json.loads(response.choices[0].message.content)
    return response_json["query"]

def process_response(response_action, response_html):
    """Process the response from the RAG system to extract filepath"""
    # Initialize OpenAI client
    client = OpenAI(api_key="OPENAI_API_KEY")
    
    prompt = f"""Compare and extract the most likely filepath from these two responses. Return it in JSON format with a 'filepath' key.
    
Response Action: {response_action}
Response HTML: {response_html}

Analysis rules:
1. If both responses contain the same filepath, use that filepath
2. If one response has a filepath and the other doesn't, use the available filepath
3. If responses have different filepaths, analyze which seems more relevant and choose one
4. If no filepath is found in either response, return "no filepath found"

Example output formats:
{{"filepath": "path/to/file.tsx"}}
{{"filepath": "no filepath found"}}

Please analyze both responses carefully and return the most appropriate filepath.
"""

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0
    )
    
    response_json = json.loads(completion.choices[0].message.content)
    return response_json["filepath"]

def enrich_html_query(target_html, target_context_html):
    """Enrich target HTML with context and generate a query"""
    client = OpenAI(api_key="OPENAI_API_KEY")

    prompt = f"""Given this HTML element:
{target_html}

And its surrounding context:
{target_context_html}

Analyze the HTML element and its surrounding context. If the HTML element alone is not descriptive enough, incorporate key details from the surrounding context. Create a concise search query to find the source file responsible for rendering this UI component.

The query should focus on distinctive UI elements, class names, or functionality. Keep it brief but informative.

Return response in JSON format:
{{
    "query": "what file is responsible for rendering [short enriched HTML]"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    response_json = json.loads(response.choices[0].message.content)
    return response_json["query"]

# Read and process filtered messages
output_results = []
with open('filtered_messages.jsonl', 'r') as f:
    for line in f:
        message = json.loads(line)
        body = json.loads(message['body'])
        
        # Process each event edit
        for event in body['event_edits']:

            query_action = generate_query(event['target_html'], event['target_context_html'])
            # query = f"what is the filepath of the element that (renders this html and is used to render this UI component) - {event['target_html']}"
            query_html = enrich_html_query(event['target_html'], event['target_context_html'])
            print(query_action)
            print(query_html)
            response_action = rag.query(query_action, param=QueryParam(mode="mix"))
            response_html = rag.query(query_html, param=QueryParam(mode="mix"))
            print(response_action)
            print(response_html)
            processed_response = process_response(response_action, response_html)
            result = {
                'problem_id': event['problem_id'],
                'response': processed_response,
                'query_action': query_action,
                'query_html': query_html,
                "raw_response_action": response_action,
                "raw_response_html": response_html
            }
            print("problem_id: ", event['problem_id'],"           processed_response: ", processed_response)
            # Write result immediately after processing
            with open('query_result.jsonl', 'a') as f:
                json.dump(result, f)
                f.write('\n')
            output_results.append(result)


print(f"Time taken to index: {end_time - start_time:.2f} seconds")
print("total time taken: ", time.time() - start_time)