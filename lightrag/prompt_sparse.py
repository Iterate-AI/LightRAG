GRAPH_FIELD_SEP = "<SEP>"

PROMPTS = {}

PROMPTS["DEFAULT_LANGUAGE"] = "English"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

PROMPTS["DEFAULT_ENTITY_TYPES"] = [
    "function",          # Any reusable function/utility/hook
    "ui_component",      # Visible UI elements and components
    "mixpanel"         # Analytics and tracking
]

PROMPTS["entity_extraction"] = """-Goal-
Given a React/Frontend code snippet, only extract major entities focus on entities that renders something and their relationships to construct a knowledge graph of the codebase.
Use {language} as output language.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity (e.g., component name, hook name)
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description including:
  * Purpose and functionality
  * Props/parameters it accepts
  * State management approach
  * Key dependencies
  * Notable patterns used
  * Implementation type/category (e.g., functional component, class component)
  * Its role in the UI, and what does it renders
  * Mixpanel related detailed information if mixpanel is present
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score (1-10) indicating strength of the relationship between the source entity and target entity
- relationship_keywords: one or more high-level key words that summarize the relationship type, choosing from:
  * IMPORTS: Component/module imports
  * RENDERS: Parent-child rendering
  * PROVIDES_CONTEXT: Context providing
  * CONSUMES_CONTEXT: Context consumption
  * PASSES_PROPS: Props passing
  * CALLS_HOOK: Hook usage
  * HANDLES_EVENT: Event handling
  * UPDATES_STATE: State updates
  * STYLES_COMPONENT: Styling relationships
  * ROUTES_TO: Routing connections
  * TESTS: Testing relationships
  * CUSTOM:<relationship_name>: For relationships that don't fit the predefined types
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify code-level patterns and architectural concepts present in the code.
Format as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in {language} as a list using **{record_delimiter}** as delimiter.

5. When finished, output {completion_delimiter}

######################
-Examples-
######################
{examples}

#############################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:
"""
PROMPTS["entity_extraction_examples"] = [
    """Example 1:

Entity_types: [function, ui_component, mixpanel]
Text: 
function UserProfile({{ userId, theme }}) {{
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {{
        async function fetchUserData() {{
            setLoading(true);
            const data = await getUserById(userId);
            setUser(data);
            setLoading(false);
        }}
        fetchUserData();
    }}, [userId]);

    if (loading) return <Spinner />;
    
    return (
        <Card className={{styles.profileCard}}>
            <UserAvatar src={{user.avatar}} />
            <UserDetails user={{user}} theme={{theme}} />
        </Card>
    );
}}

################
Output:
("entity"{tuple_delimiter}"UserProfile"{tuple_delimiter}"function"{tuple_delimiter}"React functional component that manages user profile data fetching and display. Handles loading states and user data through hooks."){record_delimiter}
("entity"{tuple_delimiter}"fetchUserData"{tuple_delimiter}"function"{tuple_delimiter}"Internal async function that handles user data fetching and state updates."){record_delimiter}
("entity"{tuple_delimiter}"Spinner"{tuple_delimiter}"ui_component"{tuple_delimiter}"Loading indicator component displayed during data fetching states."){record_delimiter}
("entity"{tuple_delimiter}"Card"{tuple_delimiter}"ui_component"{tuple_delimiter}"Container component that wraps profile content with styling."){record_delimiter}
("entity"{tuple_delimiter}"UserAvatar"{tuple_delimiter}"ui_component"{tuple_delimiter}"Visual component displaying the user's avatar image."){record_delimiter}
("entity"{tuple_delimiter}"UserDetails"{tuple_delimiter}"ui_component"{tuple_delimiter}"Component that renders detailed user information with theme support."){record_delimiter}
("relationship"{tuple_delimiter}"UserProfile"{tuple_delimiter}"fetchUserData"{tuple_delimiter}"UserProfile contains and calls fetchUserData for data fetching"{tuple_delimiter}"CALLS_HOOK"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"UserProfile"{tuple_delimiter}"Spinner"{tuple_delimiter}"UserProfile conditionally renders Spinner during loading"{tuple_delimiter}"RENDERS"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"UserProfile"{tuple_delimiter}"Card"{tuple_delimiter}"UserProfile renders Card as main container"{tuple_delimiter}"RENDERS"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Card"{tuple_delimiter}"UserAvatar"{tuple_delimiter}"Card renders UserAvatar as child component"{tuple_delimiter}"RENDERS"{tuple_delimiter}6){record_delimiter}
("relationship"{tuple_delimiter}"Card"{tuple_delimiter}"UserDetails"{tuple_delimiter}"Card renders UserDetails as child component"{tuple_delimiter}"RENDERS"{tuple_delimiter}6){record_delimiter}
("content_keywords"{tuple_delimiter}"functional components, async operations, component hierarchy, conditional rendering"){completion_delimiter}
#############################""",

    """Example 2:

Entity_types: [function, ui_component, mixpanel]
Text: 
const useAuth = () => {{
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const navigate = useNavigate();

    const login = async (credentials) => {{
        try {{
            const response = await authService.login(credentials);
            setUser(response.user);
            setIsAuthenticated(true);
            navigate('/dashboard');
        }} catch (error) {{
            throw new Error('Authentication failed');
        }}
    }};

    const logout = () => {{
        setUser(null);
        setIsAuthenticated(false);
        navigate('/login');
    }};

    return {{ user, isAuthenticated, login, logout }};
}};
""" + """
################
Output:
("entity"{tuple_delimiter}"useAuth"{tuple_delimiter}"function"{tuple_delimiter}"Custom hook managing authentication state and operations. Provides login/logout functionality with navigation."){record_delimiter}
("entity"{tuple_delimiter}"login"{tuple_delimiter}"function"{tuple_delimiter}"Async function handling user authentication, state updates, and navigation."){record_delimiter}
("entity"{tuple_delimiter}"logout"{tuple_delimiter}"function"{tuple_delimiter}"Function handling user logout process, state clearing, and navigation."){record_delimiter}
("entity"{tuple_delimiter}"authService.login"{tuple_delimiter}"function"{tuple_delimiter}"External authentication service function for user login."){record_delimiter}
("relationship"{tuple_delimiter}"useAuth"{tuple_delimiter}"login"{tuple_delimiter}"useAuth contains and exposes login function"{tuple_delimiter}"CALLS_HOOK"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"useAuth"{tuple_delimiter}"logout"{tuple_delimiter}"useAuth contains and exposes logout function"{tuple_delimiter}"CALLS_HOOK"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"login"{tuple_delimiter}"authService.login"{tuple_delimiter}"login function calls authService.login"{tuple_delimiter}"CALLS_HOOK"{tuple_delimiter}8){record_delimiter}
("content_keywords"{tuple_delimiter}"custom hooks, authentication flow, state management, navigation"){completion_delimiter}
#############################"""]

PROMPTS[
    "summarize_entity_descriptions"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or two React components, hooks, or other frontend entities, and a list of descriptions related to them.
Please concatenate all of these into a single, comprehensive description. Make sure to include:

- Core functionality and purpose
- Props/parameters accepted and their usage
- State management approach and any hooks used
- Key dependencies and imported functions/components
- CSS/styling details including:
  * CSS classes and styles applied
  * Layout and positioning
  * Responsive design considerations
  * Visual effects and animations
- What the component renders (DOM elements, child components)
- Notable patterns or implementation approaches used
- Event handlers and user interactions

Make sure to include the component/hook names so we have the full context and output a very short concentrated and concise description.
Use {language} as output language.

#######
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""

PROMPTS[
    "entiti_continue_extraction"
] = """MANY React components, hooks, and frontend entities were missed in the last extraction. Add them below using the same format:
"""

PROMPTS[
    "entiti_if_loop_extraction"
] = """It appears some React components, hooks or frontend entities may have still been missed. Answer YES | NO if there are still entities that need to be added.
"""

PROMPTS["fail_response"] = "Sorry, I'm not able to provide an answer about that React component or frontend functionality."

PROMPTS["rag_response"] = """---Role---

You are a helpful assistant responding to questions about React components and frontend code in the data tables provided.


---Goal---

Generate a response of the target length and format that responds to the user's question about React components and frontend code, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge about React and frontend development.
If you don't know the answer, just say so. Do not make anything up.
Do not include information where the supporting evidence for it is not provided.

When handling relationships with timestamps:
1. Each relationship between components/hooks has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting relationships, consider both the semantic content and the timestamp
3. Don't automatically prefer the most recently created relationships - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Target response length and format---

{response_type}

---Data tables---

{context_data}

Add sections and commentary to the response as appropriate for the length and format. Style the response in markdown."""

PROMPTS["keywords_extraction"] = """---Role---

You are a helpful assistant tasked with identifying both high-level and low-level keywords in React and frontend-related queries.

---Goal---

Given the query about React components or frontend code, list both high-level and low-level keywords. High-level keywords focus on overarching concepts or patterns, while low-level keywords focus on specific components, hooks, props, or implementation details.

---Instructions---

- Output the keywords in JSON format.
- The JSON should have two keys:
  - "high_level_keywords" for overarching concepts or patterns.
  - "low_level_keywords" for specific components, hooks, or details.

######################
-Examples-
######################
{examples}

#############################
-Real Data-
######################
Query: {query}
######################
The `Output` should be human text, not unicode characters. Keep the same language as `Query`.
Output:

"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "How does the UserProfile component handle authentication state?"
################
Output:
{
  "high_level_keywords": ["Authentication", "State management", "Component lifecycle"],
  "low_level_keywords": ["UserProfile", "useState", "useEffect", "props", "conditional rendering"]
}
#############################""",
    """Example 2:

Query: "What are the performance implications of using React.memo in the ProductList?"
################
Output:
{
  "high_level_keywords": ["Performance optimization", "Component rendering", "Memoization"],
  "low_level_keywords": ["React.memo", "ProductList", "re-renders", "props comparison", "useMemo"]
}
#############################""",
    """Example 3:

Query: "How is form validation implemented in the SignupForm component?"
################
Output:
{
  "high_level_keywords": ["Form handling", "Validation", "User input"],
  "low_level_keywords": ["SignupForm", "useForm", "validation rules", "error messages", "form submission"]
}
#############################""",
]


PROMPTS["naive_rag_response"] = """---Role---

You are a helpful assistant responding to questions about React components and frontend code documentation.


---Goal---

Generate a response of the target length and format that responds to the user's question about frontend development, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge about React and web development.
If you don't know the answer, just say so. Do not make anything up.
Do not include information where the supporting evidence for it is not provided.

When handling content with timestamps:
1. Each piece of content has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting information, consider both the content and the timestamp
3. Don't automatically prefer the most recent content - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Target response length and format---

{response_type}

---Documents---

{content_data}

Add sections and commentary to the response as appropriate for the length and format. Style the response in markdown.
"""

PROMPTS[
    "similarity_check"
] = """Please analyze the similarity between these two React/frontend-related questions:

Question 1: {original_prompt}
Question 2: {cached_prompt}

Please evaluate the following two points and provide a similarity score between 0 and 1 directly:
1. Whether these two questions are semantically similar
2. Whether the answer to Question 2 can be used to answer Question 1
Similarity score criteria:
0: Completely unrelated or answer cannot be reused, including but not limited to:
   - The questions refer to different components/hooks
   - The components serve different purposes
   - The implementation details are different
   - The React patterns or concepts are different
   - The frontend features discussed are different
   - The context of usage is different
   - The key requirements or constraints are different
1: Identical and answer can be directly reused
0.5: Partially related and answer needs modification to be used
Return only a number between 0-1, without any additional content.
"""

PROMPTS["mix_rag_response"] = """---Role---

You are a professional assistant responsible for answering questions about React components and frontend code based on knowledge graph and textual information. Please respond in the same language as the user's question.

---Goal---

Generate a concise response that summarizes relevant points from the provided information about React and frontend development. If you don't know the answer, just say so. Do not make anything up or include information where the supporting evidence is not provided.

When handling information with timestamps:
1. Each piece of information (both relationships and content) has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting information, consider both the content/relationship and the timestamp
3. Don't automatically prefer the most recent information - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Data Sources---

1. Knowledge Graph Data:
{kg_context}

2. Vector Data:
{vector_context}

---Response Requirements---

- Target format and length: {response_type}
- Use markdown formatting with appropriate section headings
- Aim to keep content around 3 paragraphs for conciseness
- Each paragraph should be under a relevant section heading
- Each section should focus on one main point or aspect of the answer
- Use clear and descriptive section titles that reflect the content
- List up to 5 most important reference sources at the end under "References", clearly indicating whether each source is from Knowledge Graph (KG) or Vector Data (VD)
  Format: [KG/VD] Source content

Add sections and commentary to the response as appropriate for the length and format. If the provided information is insufficient to answer the question, clearly state that you don't know or cannot provide an answer in the same language as the user's question."""
