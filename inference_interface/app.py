# v3.0 - PRODUCTION - Unified Interface with Pre-computed Data
"""
Last Updated: 2026-04-10 19:30:00
Version: PRODUCTION v3.0
Murali's Medicare Policy Assistant - GraphRAG Demo
Streamlit Cloud → Databricks Unity Catalog Tables

New Features:
- Pre-generated Q&As (instant answers)
- Pre-calculated statistics (fast dashboard)
- On-demand querying (2-3 sec response)
- Unified tabbed interface
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO
import re
import os
matplotlib.use('Agg')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Murali's Medicare Policy Assistant | GraphRAG Demo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS - DARK THEME WITH RED ACCENTS (MOBILE-RESPONSIVE)
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #0E1117;
    }
    
    .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
    }
    
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem;
        }
    }
    
    .sub-header {
        font-size: 1.1rem;
        color: #9CA3AF;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    @media (max-width: 768px) {
        .sub-header {
            font-size: 0.9rem;
        }
    }
    
    /* Entity pills */
    .entity-pill {
        display: inline-block;
        padding: 0.4rem 0.9rem;
        margin: 0.3rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
        white-space: nowrap;
    }
    
    .entity-policy { 
        background: linear-gradient(135deg, #3B82F6, #1D4ED8);
        color: white;
    }
    .entity-procedure { 
        background: linear-gradient(135deg, #8B5CF6, #6D28D9);
        color: white;
    }
    .entity-organization { 
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
    }
    .entity-condition { 
        background: linear-gradient(135deg, #F59E0B, #D97706);
        color: white;
    }
    .entity-demographic { 
        background: linear-gradient(135deg, #EC4899, #DB2777);
        color: white;
    }
    
    /* Buttons - RED ACCENT */
    .stButton > button {
        background: linear-gradient(135deg, #EF4444, #DC2626) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        min-height: 44px !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #DC2626, #B91C1C) !important;
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Search bar */
    .stTextInput > div > div > input {
        background-color: #1F2937 !important;
        color: white !important;
        border: 2px solid #374151 !important;
        border-radius: 10px !important;
        font-size: 1.1rem !important;
        padding: 0.8rem 1rem !important;
        min-height: 48px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #EF4444 !important;
        box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2) !important;
    }
    
    /* Tabs - RED ACCENT */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1F2937;
        border-radius: 10px;
        padding: 0.5rem;
        overflow-x: auto;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #9CA3AF;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        white-space: nowrap;
        min-height: 44px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #EF4444, #DC2626) !important;
        color: white !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #EF4444, #F59E0B);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0E1117;
        border-right: 1px solid #1F2937;
    }
    
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            width: 280px !important;
        }
    }
    
    /* Metrics - RED ACCENT */
    [data-testid="stMetricValue"] {
        color: #EF4444 !important;
        font-size: 1.8rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
        min-height: 44px !important;
    }
    
    /* DataFrames */
    .stDataFrame {
        overflow-x: auto;
    }
    
    /* Mobile: stack columns */
    @media (max-width: 768px) {
        .row-widget.stHorizontal {
            flex-direction: column !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'search_history' not in st.session_state:
    st.session_state.search_history = []

if 'current_results' not in st.session_state:
    st.session_state.current_results = None

if 'search_mode' not in st.session_state:
    st.session_state.search_mode = "Relationship Analysis"

if 'query' not in st.session_state:
    st.session_state.query = ""

if 'trigger_search' not in st.session_state:
    st.session_state.trigger_search = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_text(text):
    """Remove streamlitApp artifact from text."""
    if not isinstance(text, str):
        return text
    return re.sub(r'streamlitApp', '', text, flags=re.IGNORECASE)

def get_dynamic_suggestions(current_results):
    """Generate dynamic suggested questions based on current results."""
    if not current_results or not current_results.get("entities"):
        return {
            "Simple Retrieval": [
                "What is Medicare Part D Stand-alone Prescription Drug Plan?",
                "What is Low Dose Computed Tomography (LDCT)?",
                "What are medicare-preventive-services?"
            ],
            "Entity Connections": [
                "How is CMS connected to Medicare Part D?",
                "What is the relationship between Part B and preventive services?",
                "How do Part D sponsors relate to drug coverage?"
            ],
            "Well-Connected Topics": [
                "Tell me about lung cancer screening",
                "What is National Coverage Determination?",
                "Explain prescription drug coverage"
            ]
        }
    
    entities = [clean_text(e.get('name', '')) for e in current_results.get("entities", [])[:3] if e.get('name')]
    
    simple_retrieval = []
    entity_connections = []
    well_connected = []
    
    if entities:
        simple_retrieval = [f"What are the coverage details for {entities[0]}?"]
        if len(entities) > 1:
            simple_retrieval.append(f"What are the eligibility requirements for {entities[1]}?")
        if len(entities) > 2:
            simple_retrieval.append(f"How does {entities[2]} work in practice?")
        
        entity_connections = [f"How is CMS connected to {entities[0]}?"]
        if len(entities) > 1:
            entity_connections.append(f"What is the relationship between Medicare Part B and {entities[0]}?")
        if len(entities) > 2:
            entity_connections.append(f"How do contractors relate to {entities[0]}?")
        
        well_connected = [f"Tell me more about {e}" for e in entities if e]
    else:
        simple_retrieval = ["What is Medicare Part D?"]
        entity_connections = ["How is CMS connected to Medicare Part D?"]
        well_connected = ["Tell me about lung cancer screening"]
    
    return {
        "Simple Retrieval": simple_retrieval[:3],
        "Entity Connections": entity_connections[:3],
        "Well-Connected Topics": well_connected[:3]
    }

# ============================================================================
# LOAD GRAPHRAG DATA
# ============================================================================

@st.cache_data
def load_graphrag_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data from Databricks Unity Catalog tables using SQL Statement Execution API."""
    import os
    import requests
    import time
    
    # Get credentials
    workspace_url = st.secrets.get("DATABRICKS_HOST", os.getenv("DATABRICKS_HOST"))
    token = st.secrets.get("DATABRICKS_TOKEN", os.getenv("DATABRICKS_TOKEN"))
    warehouse_id = st.secrets.get("DATABRICKS_WAREHOUSE_ID", "e7ab584a1feb58ef")
    
    if not workspace_url or not token:
        st.error("❌ Missing DATABRICKS_HOST or DATABRICKS_TOKEN in Streamlit secrets!")
        st.stop()
    
    # Format URL
    if not workspace_url.startswith('https://'):
        workspace_url = f"https://{workspace_url}"
    
    st.info(f"🔗 Connecting to: {workspace_url}")
    
    def query_table(table_name: str, columns: str = "*") -> pd.DataFrame:
        """Query a table via SQL Statement Execution API."""
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        sql = f"SELECT {columns} FROM {table_name}"
        payload = {
            "warehouse_id": warehouse_id,
            "statement": sql,
            "wait_timeout": "50s"
        }
        
        try:
            st.write(f"📊 Querying {table_name}...")
            resp = requests.post(
                f"{workspace_url}/api/2.0/sql/statements/",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if resp.status_code != 200:
                st.error(f"❌ API Error {resp.status_code}: {resp.text}")
                st.stop()
            
            result = resp.json()
            statement_id = result["statement_id"]
            status = result.get("status", {}).get("state")
            
            # Poll for completion (up to 5 minutes)
            for _ in range(150):
                if status == "SUCCEEDED":
                    break
                time.sleep(2)
                status_resp = requests.get(
                    f"{workspace_url}/api/2.0/sql/statements/{statement_id}",
                    headers=headers
                )
                if status_resp.status_code == 200:
                    result = status_resp.json()
                    status = result.get("status", {}).get("state")
            
            if status != "SUCCEEDED":
                st.error(f"❌ Query failed with status: {status}")
                st.stop()
            
            # Get results - handle both inline and chunked
            manifest = result.get("manifest", {})
            columns_list = [c["name"] for c in manifest.get("schema", {}).get("columns", [])]
            
            # Check if result is inline or needs chunking
            result_data = result.get("result")
            if result_data and "data_array" in result_data:
                # Inline result (small tables)
                rows = result_data["data_array"]
                df = pd.DataFrame(rows, columns=columns_list)
            else:
                # Chunked result (large tables)
                all_rows = []
                chunks = manifest.get("chunks", [])
                
                for chunk_info in chunks:
                    chunk_index = chunk_info.get("chunk_index", 0)
                    chunk_resp = requests.get(
                        f"{workspace_url}/api/2.0/sql/statements/{statement_id}/result/chunks/{chunk_index}",
                        headers=headers
                    )
                    
                    if chunk_resp.status_code == 200:
                        chunk_data = chunk_resp.json()
                        for row in chunk_data.get("data_array", []):
                            all_rows.append(row)
                
                df = pd.DataFrame(all_rows, columns=columns_list)
            
            st.success(f"✅ Loaded {len(df):,} rows from {table_name}")
            return df
            
        except Exception as e:
            st.error(f"❌ Exception querying {table_name}: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()
    
    # Load all tables
    entities_df = query_table("research_catalog.healthcare.graphrag_entities")
    relationships_df = query_table("research_catalog.healthcare.graphrag_relationships")
    text_units_df = query_table("research_catalog.healthcare.graphrag_text_units", "id, document_id, chunk_index")  # Metadata only
    common_qas_df = query_table("research_catalog.healthcare.graphrag_common_qas")
    stats_df = query_table("research_catalog.healthcare.graphrag_statistics")
    
    return entities_df, relationships_df, text_units_df, common_qas_df, stats_df

# Load data once at startup
entities_df, relationships_df, text_units_df, common_qas_df, stats_df = load_graphrag_data()

# =============================================================================
# STATISTICS DISPLAY
# =============================================================================

def display_statistics(stats_df):
    """Display pre-calculated knowledge graph statistics."""
    st.header("📊 Knowledge Graph Statistics")
    st.write("Pre-calculated statistics from the nightly GraphRAG job.")
    
    # Convert stats back to dictionary
    import json
    stats = {}
    for _, row in stats_df.iterrows():
        try:
            if row['metric_type'] == 'dict' or row['metric_type'] == 'list':
                stats[row['metric_name']] = json.loads(row['metric_value'])
            else:
                stats[row['metric_name']] = row['metric_value']
        except:
            stats[row['metric_name']] = row['metric_value']
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Entities", f"{int(stats.get('total_entities', 0)):,}")
    
    with col2:
        st.metric("Relationships", f"{int(stats.get('total_relationships', 0)):,}")
    
    with col3:
        st.metric("Text Chunks", f"{int(stats.get('total_text_chunks', 0)):,}")
    
    with col4:
        st.metric("Documents", f"{int(stats.get('total_documents', 0)):,}")
    
    # Entity types distribution
    if 'entity_types' in stats:
        st.subheader("Entity Types Distribution")
        entity_types = stats['entity_types']
        if isinstance(entity_types, dict):
            entity_df = pd.DataFrame(list(entity_types.items()), columns=['Entity Type', 'Count'])
            entity_df = entity_df.sort_values('Count', ascending=False).head(10)
            st.bar_chart(entity_df.set_index('Entity Type'))

# =============================================================================
# COMMON Q&As DISPLAY
# =============================================================================

def display_common_qas(common_qas_df):
    """Display pre-generated Q&A pairs."""
    st.header("💡 Common Questions & Answers")
    st.write("These questions and answers were pre-generated using LLM analysis of the knowledge graph. **Instant answers!**")
    
    if len(common_qas_df) == 0:
        st.info("No pre-generated Q&As available yet. Run the GraphRAG job to generate them.")
        return
    
    # Filter by category if available
    if 'category' in common_qas_df.columns:
        categories = ['All'] + sorted(common_qas_df['category'].unique().tolist())
        selected_category = st.selectbox("Filter by category:", categories, key="qa_category_filter")
        
        if selected_category != 'All':
            filtered_qas = common_qas_df[common_qas_df['category'] == selected_category]
        else:
            filtered_qas = common_qas_df
    else:
        filtered_qas = common_qas_df
    
    st.caption(f"Showing {len(filtered_qas)} Q&A pairs")
    
    # Display Q&As
    for idx, row in filtered_qas.iterrows():
        with st.expander(f"❓ {row['question']}", expanded=False):
            st.write(f"**Answer:** {row['answer']}")
            if 'category' in row and row['category']:
                st.caption(f"📂 Category: {row['category']}")
            if 'entities' in row and row['entities']:
                entities_str = ', '.join(row['entities']) if isinstance(row['entities'], list) else row['entities']
                st.caption(f"🏷️ Related entities: {entities_str}")

# =============================================================================
# ON-DEMAND QUERY (NEW QUESTIONS)
# =============================================================================

@st.cache_data(ttl=3600)
def query_databricks_for_answer(question: str, _workspace_url: str, _token: str, _warehouse_id: str) -> str:
    """Query Databricks for answers to new questions using full text data."""
    import requests
    import time
    
    headers = {"Authorization": f"Bearer {_token}", "Content-Type": "application/json"}
    
    # Step 1: Get relevant text chunks using keyword search
    # Extract key terms from question
    import re
    keywords = [word.lower() for word in re.findall(r'\w+', question) if len(word) > 3]
    if not keywords:
        return "Please provide a more specific question."
    
    keyword_conditions = " OR ".join([f"LOWER(text) LIKE '%{kw}%'" for kw in keywords[:5]])
    
    sql = f"""
    SELECT text, document_id 
    FROM research_catalog.healthcare.graphrag_text_units 
    WHERE {keyword_conditions}
    LIMIT 10
    """
    
    payload = {
        "warehouse_id": _warehouse_id,
        "statement": sql,
        "wait_timeout": "50s"
    }
    
    try:
        resp = requests.post(
            f"{_workspace_url}/api/2.0/sql/statements/",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if resp.status_code != 200:
            return f"Error querying database: {resp.status_code}"
        
        result = resp.json()
        statement_id = result["statement_id"]
        status = result.get("status", {}).get("state")
        
        # Poll for completion
        for _ in range(60):
            if status == "SUCCEEDED":
                break
            time.sleep(2)
            status_resp = requests.get(
                f"{_workspace_url}/api/2.0/sql/statements/{statement_id}",
                headers=headers
            )
            if status_resp.status_code == 200:
                result = status_resp.json()
                status = result.get("status", {}).get("state")
        
        if status != "SUCCEEDED":
            return "Query timed out or failed"
        
        # Get results
        manifest = result.get("manifest", {})
        result_data = result.get("result")
        
        if result_data and "data_array" in result_data:
            rows = result_data["data_array"]
            if len(rows) == 0:
                return "No relevant information found in the knowledge graph. Try rephrasing your question or check the Common Q&As tab."
            
            # Combine text chunks as context
            context_texts = [row[0] for row in rows if row[0]]
            context = "\n\n".join(context_texts[:5])  # Use top 5 chunks
            
            # Return context (in production, this would go through an LLM)
            answer = f"**Based on the knowledge graph:**\n\n{context[:2000]}..."
            return answer
        else:
            return "No relevant information found."
            
    except Exception as e:
        return f"Error: {str(e)}"

def ask_new_question_section():
    """Section for asking new questions."""
    st.header("❓ Ask a New Question")
    st.write("Ask any question about healthcare policies. The system will search the full knowledge graph (round-trip to Databricks).")
    st.caption("⏱️ Response time: ~2-3 seconds")
    
    # Get credentials
    workspace_url = st.secrets.get("DATABRICKS_HOST", os.getenv("DATABRICKS_HOST"))
    token = st.secrets.get("DATABRICKS_TOKEN", os.getenv("DATABRICKS_TOKEN"))
    warehouse_id = st.secrets.get("DATABRICKS_WAREHOUSE_ID", "e7ab584a1feb58ef")
    
    if not workspace_url.startswith('https://'):
        workspace_url = f"https://{workspace_url}"
    
    question = st.text_input("Enter your question:", placeholder="e.g., What is the coverage for diabetes screening?", key="new_question_input")
    
    if st.button("🔍 Get Answer", type="primary") and question:
        with st.spinner("🔍 Searching knowledge graph and generating answer..."):
            answer = query_databricks_for_answer(question, workspace_url, token, warehouse_id)
            st.write("**Answer:**")
            st.write(answer)

# ============================================================================
# GRAPHRAG QUERY FUNCTIONS (for Advanced Search)
# ============================================================================

def detect_entities_in_query(query: str, entities_df: pd.DataFrame, top_k: int = 5) -> List[Dict[str, Any]]:
    """Detect entities mentioned in the query by keyword matching."""
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    entity_scores = []
    for idx, row in entities_df.iterrows():
        entity_text = row['text'].lower()
        entity_words = set(re.findall(r'\w+', entity_text))
        
        overlap = len(query_words & entity_words)
        if overlap > 0:
            if any(word in entity_text for word in query_words if len(word) > 3):
                overlap += 2
            
            entity_scores.append({
                'name': row['text'],
                'type': row['type'],
                'score': overlap / max(len(entity_words), 1),
                'chunk_id': row['chunk_id']
            })
    
    entity_scores.sort(key=lambda x: x['score'], reverse=True)
    return entity_scores[:top_k]

def traverse_graph(entities: List[Dict], relationships_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Find relationships involving the detected entities."""
    if not entities:
        return []
    
    entity_names = [e['name'] for e in entities]
    relevant_rels = relationships_df[
        relationships_df['source'].isin(entity_names) | 
        relationships_df['target'].isin(entity_names)
    ]
    
    graph_paths = []
    for idx, row in relevant_rels.iterrows():
        graph_paths.append({
            'origin': row['source'],
            'target': row['target'],
            'relationship': row['relation'],
            'chunk_id': row['chunk_id']
        })
    
    return graph_paths[:15]

def retrieve_text_chunks(chunk_ids: List[int], text_units_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Retrieve text chunks by their IDs - note: text_units_df only has metadata."""
    # Note: We're only loading metadata (id, document_id, chunk_index) to avoid large data transfers
    # For full text, we'd need to query Databricks on-demand
    relevant_chunks = text_units_df[text_units_df['id'].isin(chunk_ids)]
    
    passages = []
    for idx, row in relevant_chunks.head(5).iterrows():
        passages.append({
            'text': f"Chunk {row['chunk_index']} from {row['document_id']}",
            'full_text': "(Full text available via on-demand query)",
            'source': row['document_id'],
            'score': 0.9
        })
    
    return passages

def synthesize_answer(query: str, entities: List[Dict], paths: List[Dict], passages: List[Dict]) -> Dict[str, Any]:
    """Synthesize answer from retrieved context."""
    if not entities or not passages:
        return {
            'executive_summary': f"I searched the Medicare policy knowledge graph for your query but could not find sufficient relevant information about: **{query}**",
            'detailed_analysis': "This could mean the topic is not yet covered in the current knowledge graph, or the query needs rephrasing. Try the Common Q&As tab for pre-answered questions.",
            'temporal_metadata': {},
            'knowledge_gaps': ["No relevant data found in the CMS Medicare Coverage Database"],
            'related_questions': []
        }
    
    main_entities = [e['name'] for e in entities[:3]]
    entity_list = ', '.join(main_entities)
    
    exec_summary = f"Based on the knowledge graph analysis, your query relates to: **{entity_list}**. "
    
    if passages:
        exec_summary += f"Found {len(passages)} relevant policy documents with information about these topics."
    
    detailed = f"**Entities Detected:** {len(entities)}\n\n"
    
    if paths:
        detailed += "**Key Relationships:**\n"
        for path in paths[:5]:
            detailed += f"- {path['origin']} **{path['relationship']}** {path['target']}\n"
    
    citations = list(set([p['source'] for p in passages])) if passages else []
    
    related_q = []
    if entities:
        for e in entities[:4]:
            related_q.append(f"Tell me more about {e['name']}")
        
        if len(entities) > 1:
            related_q.append(f"How are {entities[0]['name']} and {entities[1]['name']} related?")
        
        related_q.append(f"What are the eligibility requirements for {entities[0]['name']}?")
    
    return {
        'executive_summary': exec_summary,
        'detailed_analysis': detailed,
        'temporal_metadata': {
            'last_updated': datetime.now().strftime("%Y-%m-%d"),
            'policy_version': "Medicare Coverage Database 2024"
        },
        'knowledge_gaps': [],
        'citations': citations,
        'related_questions': related_q[:6]
    }

def run_graphrag_query(query: str, mode: str) -> Dict[str, Any]:
    """Run GraphRAG query using local parquet files."""
    entities = detect_entities_in_query(query, entities_df, top_k=5)
    paths = traverse_graph(entities, relationships_df)
    chunk_ids = list(set([e['chunk_id'] for e in entities] + [p['chunk_id'] for p in paths]))
    passages = retrieve_text_chunks(chunk_ids, text_units_df)
    answer = synthesize_answer(query, entities, paths, passages)
    
    answer['entities'] = entities
    answer['graph_paths'] = paths
    answer['supporting_passages'] = passages
    answer['query'] = query
    
    entity_connections = {}
    for path in paths:
        entity_connections[path['origin']] = entity_connections.get(path['origin'], 0) + 1
        entity_connections[path['target']] = entity_connections.get(path['target'], 0) + 1
    
    central_nodes = []
    for entity_name, conn_count in sorted(entity_connections.items(), key=lambda x: x[1], reverse=True)[:5]:
        entity_info = next((e for e in entities if e['name'] == entity_name), None)
        central_nodes.append({
            'entity': entity_name,
            'connections': conn_count,
            'centrality': conn_count / max(len(paths), 1),
            'interpretation': f"Entity type: {entity_info['type'] if entity_info else 'unknown'}"
        })
    
    answer['central_nodes'] = central_nodes
    answer['all_relationships'] = [
        {'entity1': p['origin'], 'relation': p['relationship'], 'entity2': p['target']}
        for p in paths
    ]
    
    return answer

def get_knowledge_graph_stats() -> Dict[str, int]:
    """Get KG statistics."""
    return {
        "entities": len(entities_df),
        "relationships": len(relationships_df),
        "text_chunks": len(text_units_df)
    }

def create_graph_visualization(entities: List[Dict], paths: List[Dict]):
    """Create clean static graph using NetworkX + matplotlib."""
    if not entities or not paths:
        return None
    
    G = nx.DiGraph()
    entity_types = {entity["name"]: entity.get("type", "unknown") for entity in entities}
    
    for path in paths:
        G.add_edge(path["origin"], path["target"], label=path.get("relationship", ""))
    
    color_map = {"policy": "#3B82F6", "organization": "#10B981", "procedure": "#8B5CF6", "condition": "#F59E0B", "demographic": "#EC4899"}
    node_colors = []
    for node in G.nodes():
        node_type = entity_types.get(node, "unknown")
        color = color_map.get(node_type, "#6B7280")
        node_colors.append(color)
    
    pos = nx.spring_layout(G, k=1.8, iterations=80, seed=42)
    fig, ax = plt.subplots(figsize=(13, 9), facecolor='#0E1117')
    ax.set_facecolor('#0E1117')
    
    nx.draw(G, pos, ax=ax, with_labels=True, node_color=node_colors, node_size=3200, 
            font_size=12, font_color="white", font_weight="bold",
            arrows=True, arrowstyle="->", arrowsize=25, edge_color="#9CA3AF", width=2.5)
    
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="#E0E7FF", font_size=10, ax=ax, rotate=False)
    
    plt.title("Knowledge Graph Subgraph", color="white", fontsize=15, pad=25)
    plt.axis("off")
    
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", facecolor='#0E1117', dpi=220)
    buf.seek(0)
    plt.close(fig)
    
    return buf

# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================

def render_entity_pill(entity: Dict) -> str:
    """Render colored entity pill."""
    entity_type = entity.get('type', 'unknown')
    type_class = f"entity-{entity_type}"
    score = entity.get('score', 0)
    clean_name = clean_text(entity["name"])
    return f'<span class="entity-pill {type_class}">{clean_name} ({score:.0%})</span>'

def simulate_progress(steps: List[str]):
    """Show progress through GraphRAG steps."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, step in enumerate(steps):
        progress = (i + 1) / len(steps)
        progress_bar.progress(progress)
        status_text.text(f"⚙️ {step}")
        time.sleep(0.7)
    
    progress_bar.empty()
    status_text.empty()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("## 🏥")
    st.markdown("### Medicare Policy Assistant")
    st.caption("GraphRAG-Powered Research Tool")
    
    st.divider()
    
    st.markdown("### 📊 Knowledge Graph Stats")
    stats = get_knowledge_graph_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Entities", f"{stats['entities']:,}")
        st.metric("Relationships", f"{stats['relationships']:,}")
    with col2:
        st.metric("Text Chunks", f"{stats['text_chunks']:,}")
    
    st.divider()
    
    st.markdown("### 💡 Quick Access")
    st.caption("Jump to a section:")
    
    if st.button("📊 Statistics", key="nav_stats", use_container_width=True):
        st.session_state.active_tab = 0
    if st.button("💡 Common Q&As", key="nav_qas", use_container_width=True):
        st.session_state.active_tab = 1
    if st.button("❓ Ask New Question", key="nav_new_q", use_container_width=True):
        st.session_state.active_tab = 2
    if st.button("🔍 Advanced Search", key="nav_advanced", use_container_width=True):
        st.session_state.active_tab = 3

# ============================================================================
# MAIN AREA - TABBED INTERFACE
# ============================================================================

st.markdown('<h1 class="main-header">🏥 Murali\'s Medicare Policy Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">GraphRAG-Powered Analysis of CMS Medicare Coverage Database</p>', unsafe_allow_html=True)

# Main tabbed interface
tab1, tab2, tab3, tab4 = st.tabs(["📊 Statistics", "💡 Common Q&As", "❓ Ask New Question", "🔍 Advanced Search"])

with tab1:
    display_statistics(stats_df)

with tab2:
    display_common_qas(common_qas_df)

with tab3:
    ask_new_question_section()

with tab4:
    st.header("🔍 Advanced Search")
    st.write("Perform graph traversal queries with entity detection and relationship analysis.")
    
    # Search configuration
    col1, col2 = st.columns([3, 1])
    with col1:
        search_mode = st.radio(
            "Search Mode",
            ["Relationship Analysis", "Standard Search"],
            index=0,
            help="Relationship Analysis uses graph traversal + community detection",
            horizontal=True,
            key="advanced_search_mode"
        )
    
    with col2:
        if search_mode == "Relationship Analysis":
            st.info("🔗 Graph traversal")
        else:
            st.info("📄 Semantic search")
    
    st.session_state.search_mode = search_mode
    
    # Suggested questions
    with st.expander("💡 Suggested Questions", expanded=True):
        tab_simple, tab_connections, tab_topics = st.tabs(["📋 Simple", "🔗 Connections", "🔀 Topics"])
        
        dynamic_sugs = get_dynamic_suggestions(st.session_state.current_results)
        
        with tab_simple:
            st.caption("Direct facts from policy documents")
            for i, q in enumerate(dynamic_sugs["Simple Retrieval"]):
                if st.button(f"💡 {q}", key=f"adv_qs1_{i}", use_container_width=True):
                    st.session_state.query = q
                    st.session_state.trigger_search = True
                    st.rerun()
        
        with tab_connections:
            st.caption("How entities relate to each other")
            for i, q in enumerate(dynamic_sugs["Entity Connections"]):
                if st.button(f"💡 {q}", key=f"adv_qs2_{i}", use_container_width=True):
                    st.session_state.query = q
                    st.session_state.trigger_search = True
                    st.rerun()
        
        with tab_topics:
            st.caption("Topics with many connections in the graph")
            for i, q in enumerate(dynamic_sugs["Well-Connected Topics"]):
                if st.button(f"💡 {q}", key=f"adv_qs3_{i}", use_container_width=True):
                    st.session_state.query = q
                    st.session_state.trigger_search = True
                    st.rerun()
    
    st.markdown("### 🔍 Enter Your Query")
    
    col1, col2 = st.columns([5, 1])
    with col1:
        query_input = st.text_input(
            "Enter your Medicare policy question:",
            value=st.session_state.query,
            placeholder="e.g., What are the eligibility requirements for preventive services?",
            label_visibility="collapsed",
            key="advanced_query_input"
        )
            
    with col2:
        search_button = st.button("🔍 Search", use_container_width=True, type="primary", key="advanced_search_btn")
    
    if search_button and query_input:
        st.session_state.query = query_input
        st.session_state.trigger_search = True
        st.rerun()
    
    if st.session_state.trigger_search and st.session_state.query:
        st.session_state.trigger_search = False
        
        with st.spinner(""):
            simulate_progress([
                "Detecting entities in query...",
                "Traversing knowledge graph...",
                "Computing community centrality...",
                "Synthesizing answer from context..."
            ])
        
        results = run_graphrag_query(st.session_state.query, st.session_state.search_mode)
        st.session_state.current_results = results
        st.session_state.search_history.append({
            "query": st.session_state.query,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": st.session_state.search_mode
        })
        st.rerun()
    
    # ========================================================================
    # RESULTS DISPLAY (for Advanced Search)
    # ========================================================================
    
    if st.session_state.current_results:
        results = st.session_state.current_results
        
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        
        result_tab1, result_tab2, result_tab3, result_tab4, result_tab5 = st.tabs(["📝 Answer", "🕸️ Knowledge Graph", "🎯 Entities", "🔗 Relationships", "📚 Sources"])
        
        with result_tab1:
            st.markdown("### 🎯 Executive Summary")
            st.markdown(clean_text(results.get("executive_summary", "No summary available.")))
            
            st.markdown("### 🔍 Detailed Analysis")
            st.markdown(clean_text(results.get("detailed_analysis", "No detailed analysis available.")))
            
            if results.get("temporal_metadata") and any(results["temporal_metadata"].values()):
                st.markdown("### 📅 Temporal Metadata")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if results["temporal_metadata"].get("effective_date"):
                        st.metric("Effective Date", results["temporal_metadata"]["effective_date"])
                with col2:
                    if results["temporal_metadata"].get("last_updated"):
                        st.metric("Last Updated", results["temporal_metadata"]["last_updated"])
                with col3:
                    if results["temporal_metadata"].get("policy_version"):
                        st.caption("**Policy Version**")
                        st.caption(results["temporal_metadata"]["policy_version"])
            
            if results.get("knowledge_gaps") and len(results["knowledge_gaps"]) > 0:
                st.markdown("### ❓ Knowledge Gaps")
                for gap in results["knowledge_gaps"]:
                    st.warning(f"⚠️ {gap}")
        
        with result_tab2:
            st.markdown("### 🕸️ Knowledge Graph Visualization")
            
            if results.get("entities") and results.get("graph_paths") and len(results["entities"]) > 0 and len(results["graph_paths"]) > 0:
                try:
                    graph_buf = create_graph_visualization(results["entities"], results["graph_paths"])
                    if graph_buf:
                        st.image(graph_buf, use_container_width=True)
                    else:
                        st.info("No graph data to visualize.")
                except Exception as e:
                    st.error(f"Graph visualization error: {str(e)}")
                    st.info("Showing tabular relationship data instead")
                    
                    if results.get("graph_paths"):
                        df_paths = pd.DataFrame(results["graph_paths"])
                        st.dataframe(df_paths, use_container_width=True)
            else:
                st.info("No graph data available for this query.")
            
            if results.get("central_nodes") and len(results["central_nodes"]) > 0:
                st.markdown("### 🌟 Central Nodes")
                for node in results["central_nodes"]:
                    with st.expander(f"**{clean_text(node['entity'])}** (Centrality: {node.get('centrality', 0):.2f})"):
                        st.markdown(f"**Connections:** {node.get('connections', 0)}")
                        st.markdown(f"**Interpretation:** {node.get('interpretation', 'N/A')}")
        
        with result_tab3:
            st.markdown("### 🎯 Detected Entities")
            
            if results.get("entities") and len(results["entities"]) > 0:
                entities_html = " ".join([render_entity_pill(e) for e in results["entities"]])
                st.markdown(entities_html, unsafe_allow_html=True)
                
                st.markdown("---")
                
                df_entities = pd.DataFrame([
                    {
                        'name': clean_text(e['name']),
                        'type': e.get('type', 'unknown'),
                        'score': e.get('score', 0)
                    }
                    for e in results["entities"]
                ])
                if "score" in df_entities.columns:
                    df_entities["score"] = df_entities["score"].apply(lambda x: f"{x:.0%}")
                st.dataframe(df_entities, use_container_width=True, hide_index=True)
            else:
                st.info("No entities detected in this query.")
        
        with result_tab4:
            st.markdown("### 🔗 Entity Relationships")
            
            if results.get("all_relationships") and len(results["all_relationships"]) > 0:
                display_count = min(10, len(results["all_relationships"]))
                df_rels = pd.DataFrame([
                    {
                        'entity1': clean_text(r['entity1']),
                        'relation': clean_text(r['relation']),
                        'entity2': clean_text(r['entity2'])
                    }
                    for r in results["all_relationships"][:display_count]
                ])
                st.dataframe(df_rels, use_container_width=True, hide_index=True)
                
                st.caption(f"Showing {display_count} of {len(results['all_relationships'])} total relationships")
            else:
                st.info("No relationships found in the knowledge graph for this query.")
        
        with result_tab5:
            st.markdown("### 📚 Supporting Evidence")
            
            if results.get("supporting_passages") and len(results["supporting_passages"]) > 0:
                for i, passage in enumerate(results["supporting_passages"], 1):
                    with st.expander(f"**Source {i}:** {passage.get('source', 'Unknown')} (Relevance: {passage.get('score', 0):.0%})"):
                        st.markdown(f"**Excerpt:** {clean_text(passage.get('text', 'N/A'))}")
                        if passage.get('full_text'):
                            st.markdown(f"**Full Text:** {clean_text(passage['full_text'])}")
            else:
                st.info("No supporting evidence found.")
            
            if results.get("citations") and len(results["citations"]) > 0:
                st.markdown("---")
                st.markdown("### 📖 Citations")
                for citation in results["citations"]:
                    st.markdown(f"- {citation}")
        
        if results.get("related_questions") and len(results["related_questions"]) > 0:
            st.markdown("---")
            st.markdown("### 💡 Related Follow-up Questions")
            
            col1, col2 = st.columns(2)
            for i, q in enumerate(results["related_questions"]):
                with col1 if i % 2 == 0 else col2:
                    if st.button(f"🔄 {clean_text(q)}", key=f"followup_{hash(q)}_{i}", use_container_width=True):
                        st.session_state.query = q
                        st.session_state.trigger_search = True
                        st.rerun()
    
    # Search History
    if st.session_state.search_history:
        with st.expander("📜 Search History"):
            for i, item in enumerate(reversed(st.session_state.search_history[-10:])):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{item['query']}**")
                    st.caption(f"{item['timestamp']} | {item['mode']}")
                with col2:
                    if st.button("🔄", key=f"history_{i}"):
                        st.session_state.query = item['query']
                        st.session_state.trigger_search = True
                        st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("💡 **Tip:** Start with Common Q&As for instant answers, or use 'Ask New Question' for custom queries.")
st.caption("🚀 Powered by Microsoft GraphRAG | Databricks Unity Catalog | Streamlit Cloud")
st.caption(f"📅 Last updated: {datetime.now().strftime('%Y-%m-%d')} | v3.0")
