"""
Healthcare Policy Assistant - Streamlit Cloud Production
100% SQL-based data loading via Databricks SQL Warehouse
Author: Murali (Engineering & Analytics Manager)
"""

import streamlit as st
import pandas as pd
import re
from openai import OpenAI
from difflib import SequenceMatcher
from typing import List, Tuple, Dict, Any
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict
from datetime import datetime, timedelta
import uuid
from databricks import sql

# ============================================================================
# CONFIGURATION
# ============================================================================

# Page configuration
st.set_page_config(
    page_title="Regulatory Intelligence Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Delta Table Names (Full Namespace)
CATALOG = "research_catalog"
SCHEMA = "healthcare"
ENTITIES_TABLE = f"{CATALOG}.{SCHEMA}.graphrag_entities"
RELATIONSHIPS_TABLE = f"{CATALOG}.{SCHEMA}.graphrag_relationships"
TEXT_UNITS_TABLE = f"{CATALOG}.{SCHEMA}.graphrag_text_units"
COMMON_QAS_TABLE = f"{CATALOG}.{SCHEMA}.graphrag_common_qas"

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main-header {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        color: #1f77b4;
        margin-top: 3rem;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 3rem;
    }
    .source-box {
        background-color: #f0f2f6;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .entity-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        margin: 0.25rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .entity-policy { background-color: #e3f2fd; color: #1976d2; }
    .entity-procedure { background-color: #f3e5f5; color: #7b1fa2; }
    .entity-organization { background-color: #e8f5e9; color: #388e3c; }
    .entity-condition { background-color: #fff3e0; color: #f57c00; }
    .reasoning-step {
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    def __init__(self, max_requests=10, time_window_minutes=5):
        self.max_requests = max_requests
        self.time_window = timedelta(minutes=time_window_minutes)
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier):
        now = datetime.now()
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.time_window
        ]
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(now)
            return True
        return False
    
    def get_remaining(self, identifier):
        now = datetime.now()
        recent = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.time_window
        ]
        return max(0, self.max_requests - len(recent))

rate_limiter = RateLimiter(max_requests=10, time_window_minutes=5)

def get_client_id():
    if 'client_id' not in st.session_state:
        st.session_state.client_id = str(uuid.uuid4())
    return st.session_state.client_id

def check_rate_limit():
    client_id = get_client_id()
    if not rate_limiter.is_allowed(client_id):
        remaining_time = rate_limiter.time_window.total_seconds() / 60
        st.error(f"🚫 Rate limit exceeded! Please wait {remaining_time:.0f} minutes.")
        st.stop()
    remaining = rate_limiter.get_remaining(client_id)
    if remaining <= 3:
        st.caption(f"⚠️ {remaining} requests remaining")

# ============================================================================
# SQL WAREHOUSE CONNECTION (100% SQL-BASED)
# ============================================================================

@st.cache_resource
def get_databricks_connection():
    """Create Databricks SQL Warehouse connection using st.secrets."""
    try:
        # Get credentials from Streamlit secrets
        host = st.secrets["DATABRICKS_HOST"]
        token = st.secrets["DATABRICKS_TOKEN"]
        warehouse_id = st.secrets["DATABRICKS_WAREHOUSE_ID"]
        
        # Create connection
        connection = sql.connect(
            server_hostname=host,
            http_path=f"/sql/1.0/warehouses/{warehouse_id}",
            access_token=token
        )
        
        return connection
    except KeyError as e:
        st.error(f"❌ Missing secret: {e}")
        st.error("Please configure DATABRICKS_HOST, DATABRICKS_TOKEN, and DATABRICKS_WAREHOUSE_ID in Streamlit secrets.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Failed to connect to Databricks: {e}")
        st.stop()

def query_table(sql_query: str) -> pd.DataFrame:
    """Execute SQL query and return DataFrame."""
    try:
        connection = get_databricks_connection()
        cursor = connection.cursor()
        cursor.execute(sql_query)
        
        # Fetch results
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=columns)
        cursor.close()
        
        return df
    except Exception as e:
        st.error(f"❌ SQL query failed: {e}")
        st.error(f"Query: {sql_query}")
        return pd.DataFrame()

# ============================================================================
# DATA LOADING (100% SQL-BASED)
# ============================================================================

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_entities():
    """Load entities from Delta table via SQL."""
    query = f"SELECT * FROM {ENTITIES_TABLE}"
    df = query_table(query)
    
    if df.empty:
        st.warning(f"⚠️ No entities found in {ENTITIES_TABLE}")
    
    return df

@st.cache_data(ttl=3600)
def load_relationships():
    """Load relationships from Delta table via SQL."""
    query = f"SELECT * FROM {RELATIONSHIPS_TABLE}"
    df = query_table(query)
    
    if df.empty:
        st.warning(f"⚠️ No relationships found in {RELATIONSHIPS_TABLE}")
    
    return df

@st.cache_data(ttl=3600)
def load_text_units():
    """Load text units from Delta table via SQL."""
    query = f"SELECT * FROM {TEXT_UNITS_TABLE}"
    df = query_table(query)
    
    if df.empty:
        st.warning(f"⚠️ No text units found in {TEXT_UNITS_TABLE}")
    
    return df

@st.cache_data(ttl=3600)
def load_common_qas():
    """Load common Q&As from Delta table via SQL."""
    try:
        query = f"SELECT * FROM {COMMON_QAS_TABLE}"
        df = query_table(query)
        return df
    except:
        # Table might not exist yet
        return pd.DataFrame()

def load_all_data():
    """Load all GraphRAG data from Delta tables."""
    with st.spinner("📊 Loading knowledge graph from Databricks..."):
        entities_df = load_entities()
        relationships_df = load_relationships()
        text_units_df = load_text_units()
        qas_df = load_common_qas()
        
        if entities_df.empty or relationships_df.empty or text_units_df.empty:
            st.error("❌ Failed to load required data from Databricks.")
            st.error("Please ensure the following tables exist:")
            st.error(f"  • {ENTITIES_TABLE}")
            st.error(f"  • {RELATIONSHIPS_TABLE}")
            st.error(f"  • {TEXT_UNITS_TABLE}")
            st.stop()
        
        st.success(f"✅ Loaded {len(entities_df):,} entities, {len(relationships_df):,} relationships, {len(text_units_df):,} text units")
        
        # Determine text column
        text_col = "text" if "text" in text_units_df.columns else text_units_df.columns[0]
        
        return {
            "entities": entities_df,
            "relationships": relationships_df,
            "text_units": text_units_df,
            "qas": qas_df,
            "text_column": text_col
        }

# ============================================================================
# OPENAI CLIENT (FOR LLM)
# ============================================================================

@st.cache_resource
def initialize_openai_client():
    """Initialize OpenAI client for Databricks Foundation Models."""
    try:
        host = st.secrets["DATABRICKS_HOST"]
        token = st.secrets["DATABRICKS_TOKEN"]
        
        client = OpenAI(
            api_key=token,
            base_url=f"https://{host}/serving-endpoints"
        )
        return client
    except Exception as e:
        st.error(f"Failed to initialize LLM client: {e}")
        return None

# ============================================================================
# TEXT PROCESSING
# ============================================================================

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[-_/]', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ============================================================================
# SEARCH FUNCTIONS
# ============================================================================

def search_text_chunks(query: str, kg_data: Dict, top_k: int = 5) -> List[Dict[str, Any]]:
    """Find relevant text chunks using keyword matching."""
    text_units_df = kg_data["text_units"]
    text_col = kg_data["text_column"]
    
    query_lower = query.lower()
    query_normalized = normalize_text(query)
    query_words = set(query_normalized.split())
    
    results = []
    
    for idx, row in text_units_df.iterrows():
        chunk_text = str(row[text_col])
        chunk_normalized = normalize_text(chunk_text)
        chunk_words = set(chunk_normalized.split())
        
        # Word overlap scoring
        overlap = len(query_words & chunk_words)
        score = overlap / max(len(query_words), 1)
        
        # Exact phrase bonus
        if query_lower in chunk_text.lower():
            score += 0.5
        
        if score > 0:
            results.append({
                "chunk_id": idx,
                "text": chunk_text,
                "score": score,
                "document_id": row.get("document_id", "unknown"),
                "source_manual": row.get("source_manual", "Unknown Manual")
            })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

def find_entities_in_query(query: str, kg_data: Dict, threshold: float = 0.3) -> List[Tuple[str, str, float]]:
    """Find entities mentioned in query."""
    entities_df = kg_data["entities"]
    query_lower = query.lower()
    query_normalized = normalize_text(query)
    query_words = set(query_normalized.split())
    
    matches = []
    
    for _, entity in entities_df.iterrows():
        entity_text = entity['text']
        entity_lower = entity_text.lower()
        entity_normalized = normalize_text(entity_text)
        entity_words = set(entity_normalized.split())
        
        # Exact match
        if entity_lower in query_lower or query_lower in entity_lower:
            matches.append((entity_text, entity['type'], 1.0))
            continue
        
        # Word overlap
        overlap = len(entity_words & query_words)
        if overlap > 0:
            score = overlap / max(len(entity_words), len(query_words))
            if score >= threshold:
                matches.append((entity_text, entity['type'], score))
    
    # Deduplicate
    seen = set()
    unique_matches = []
    for match in matches:
        if match[0] not in seen:
            seen.add(match[0])
            unique_matches.append(match)
    
    unique_matches.sort(key=lambda x: x[2], reverse=True)
    return unique_matches[:10]

def find_relationships(entity_names: List[str], kg_data: Dict) -> List[Dict[str, Any]]:
    """Find relationships involving given entities."""
    relationships_df = kg_data["relationships"]
    entity_names_lower = [e.lower() for e in entity_names]
    
    relevant_rels = []
    for _, rel in relationships_df.iterrows():
        source_lower = rel['source'].lower()
        target_lower = rel['target'].lower()
        
        for entity in entity_names_lower:
            if entity in source_lower or entity in target_lower:
                relevant_rels.append({
                    "source": rel['source'],
                    "target": rel['target'],
                    "relation": rel['relation'],
                    "chunk_id": rel.get('chunk_id', None)
                })
                break
    
    return relevant_rels

def get_chunks_from_relationships(relationships: List[Dict], kg_data: Dict) -> List[Dict[str, Any]]:
    """Get text chunks containing relationships."""
    if not relationships:
        return []
    
    text_units_df = kg_data["text_units"]
    text_col = kg_data["text_column"]
    chunk_ids = set(rel['chunk_id'] for rel in relationships if rel.get('chunk_id') is not None)
    
    chunks = []
    for chunk_id in chunk_ids:
        if chunk_id < len(text_units_df):
            row = text_units_df.iloc[chunk_id]
            chunks.append({
                "chunk_id": chunk_id,
                "text": str(row[text_col]),
                "document_id": row.get("document_id", "unknown"),
                "source_manual": row.get("source_manual", "Unknown")
            })
    
    return chunks

# ============================================================================
# LLM ANSWER GENERATION
# ============================================================================

def generate_answer_with_citations(query: str, chunks: List[Dict], entities: List[Tuple], 
                                   relationships: List[Dict], client: OpenAI) -> Tuple[str, str]:
    """Generate answer using LLM with citations."""
    if not chunks:
        return "No relevant information found in policy documents.", "No analysis available."
    
    # Build context
    context_parts = ["RELEVANT POLICY EXCERPTS:\n"]
    for i, chunk in enumerate(chunks[:3], 1):
        context_parts.append(f"[Source {i}] ({chunk.get('source_manual', 'Unknown')})\n{chunk['text'][:800]}\n")
    
    if relationships:
        context_parts.append("\nKNOWLEDGE GRAPH RELATIONSHIPS:\n")
        for rel in relationships[:10]:
            context_parts.append(f"- {rel['source']} → {rel['relation']} → {rel['target']}")
    
    context = "\n".join(context_parts)
    
    system_prompt = """You are a Medicare policy expert assistant.
Answer questions using provided policy excerpts and relationships.
Use **[Source N]** format for citations."""
    
    user_prompt = f"""Context:\n{context}\n\nQuestion: {query}\n\nProvide a clear answer with **bolded citations**."""
    
    try:
        response = client.chat.completions.create(
            model="databricks-meta-llama-3-3-70b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=700,
            temperature=0.2
        )
        answer = response.choices[0].message.content
        
        # Generate reasoning
        reasoning = generate_reasoning_path(query, entities, relationships, chunks)
        
        return answer, reasoning
    except Exception as e:
        return f"Error generating answer: {e}", "Error in analysis."

def generate_reasoning_path(query: str, entities: List[Tuple], relationships: List[Dict], chunks: List[Dict]) -> str:
    """Generate 3-step reasoning path."""
    steps = []
    
    if entities:
        entity_names = [e[0] for e in entities[:3]]
        steps.append(f"**Step 1: Entity Detection**\n"
                    f"Identified: {', '.join(entity_names)}.")
    else:
        steps.append("**Step 1: Keyword Analysis**\n"
                    "Analyzed query for relevant keywords.")
    
    if relationships:
        steps.append(f"**Step 2: Relationship Exploration**\n"
                    f"Found {len(relationships)} relationships. "
                    f"Example: {relationships[0]['source']} → {relationships[0]['relation']} → {relationships[0]['target']}")
    else:
        steps.append("**Step 2: Document Search**\n"
                    "Searched policy documents for passages.")
    
    source_manuals = set(c.get('source_manual', 'Unknown') for c in chunks)
    steps.append(f"**Step 3: Evidence Synthesis**\n"
                f"Found {len(chunks)} passages from {len(source_manuals)} manual(s).")
    
    return "\n\n".join(steps)

# ============================================================================
# GRAPH VISUALIZATION
# ============================================================================

def create_knowledge_graph_viz(entities: List[Tuple], relationships: List[Dict]) -> plt.Figure:
    """Create NetworkX graph visualization."""
    G = nx.Graph()
    
    color_map = {
        'policy': '#1976d2',
        'procedure': '#7b1fa2',
        'organization': '#388e3c',
        'condition': '#f57c00',
        'default': '#666666'
    }
    
    entity_colors = {}
    for entity_text, entity_type, score in entities:
        G.add_node(entity_text)
        entity_colors[entity_text] = color_map.get(entity_type.lower(), color_map['default'])
    
    for rel in relationships[:20]:
        if rel['source'] in G.nodes and rel['target'] in G.nodes:
            G.add_edge(rel['source'], rel['target'])
    
    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    
    node_colors = [entity_colors.get(node, color_map['default']) for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1200, alpha=0.9, ax=ax)
    nx.draw_networkx_edges(G, pos, width=2, alpha=0.5, edge_color='#999', ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold', ax=ax)
    
    ax.set_title("Knowledge Graph: Entity Relationships", fontsize=16, fontweight='bold')
    ax.axis('off')
    plt.tight_layout()
    
    return fig

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Initialize session state
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    
    # Load data and clients
    kg_data = load_all_data()
    client = initialize_openai_client()
    
    if client is None:
        st.error("Failed to initialize LLM client.")
        st.stop()
    
    # ========================================================================
    # SIDEBAR
    # ========================================================================
    
    with st.sidebar:
        with st.expander("🛠️ System Architecture", expanded=False):
            st.markdown("**Author:** Murali")
            st.markdown("**Backend:** Databricks + GraphRAG")
            st.markdown("**Frontend:** Streamlit Cloud")
        
        with st.expander("📊 System Metrics", expanded=False):
            st.metric("Entities", len(kg_data["entities"]))
            st.metric("Relationships", len(kg_data["relationships"]))
            st.metric("Text Chunks", len(kg_data["text_units"]))
    
    # ========================================================================
    # LANDING PAGE
    # ========================================================================
    
    if not st.session_state.show_results:
        st.markdown('<div class="main-header">🧠 Regulatory Intelligence Engine</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">GraphRAG-powered CMS Medicare Policy Intelligence</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            query = st.text_input(
                "What would you like to know?",
                value=st.session_state.search_query,
                placeholder="Ask about Medicare policies, coverage, or compliance...",
                label_visibility="collapsed",
                key="main_search"
            )
            
            search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
        
        # Guided Discovery
        st.markdown("### 🎯 Guided Discovery")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 Coverage Policies", use_container_width=True):
                st.session_state.search_query = "What are the coverage requirements for preventive screening services?"
                st.session_state.show_results = True
                st.rerun()
        
        with col2:
            if st.button("🔗 Policy Relations", use_container_width=True):
                st.session_state.search_query = "How are NCDs and local coverage determinations related?"
                st.session_state.show_results = True
                st.rerun()
        
        with col3:
            if st.button("✅ Code Compliance", use_container_width=True):
                st.session_state.search_query = "What HCPCS codes are required for lung cancer screening?"
                st.session_state.show_results = True
                st.rerun()
        
        with col4:
            if st.button("📊 2026 Updates", use_container_width=True):
                st.session_state.search_query = "What policy changes are effective in 2026?"
                st.session_state.show_results = True
                st.rerun()
        
        if search_clicked and query:
            st.session_state.search_query = query
            st.session_state.show_results = True
            st.rerun()
    
    # ========================================================================
    # RESULTS VIEW
    # ========================================================================
    
    else:
        query = st.session_state.search_query
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            if st.button("← Back"):
                st.session_state.show_results = False
                st.rerun()
        with col2:
            st.markdown(f"### 🔍 Results for: *{query}*")
        
        check_rate_limit()
        
        with st.spinner("Analyzing..."):
            chunks = search_text_chunks(query, kg_data, top_k=5)
            entities = find_entities_in_query(query, kg_data, threshold=0.3)
            entity_names = [e[0] for e in entities]
            relationships = find_relationships(entity_names, kg_data)
            
            if relationships:
                rel_chunks = get_chunks_from_relationships(relationships, kg_data)
                all_chunk_ids = set(c['chunk_id'] for c in chunks)
                for rc in rel_chunks:
                    if rc['chunk_id'] not in all_chunk_ids:
                        chunks.append(rc)
            
            answer, reasoning = generate_answer_with_citations(query, chunks, entities, relationships, client)
        
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Analysis", "🧭 Reasoning", "🕸️ Graph", "📚 Evidence"])
        
        with tab1:
            st.markdown("### 💡 Analysis")
            st.markdown(answer)
        
        with tab2:
            st.markdown("### 🧭 Analysis Path")
            st.markdown(reasoning)
        
        with tab3:
            st.markdown("### 🕸️ Knowledge Graph")
            if entities and relationships:
                try:
                    fig = create_knowledge_graph_viz(entities, relationships)
                    st.pyplot(fig)
                    plt.close(fig)
                except Exception as e:
                    st.error(f"Visualization error: {e}")
            else:
                st.info("No graph relationships found.")
        
        with tab4:
            st.markdown("### 📚 Evidence")
            if entities:
                st.markdown("**Entities**")
                entity_df = pd.DataFrame(entities, columns=['Entity', 'Type', 'Confidence'])
                st.dataframe(entity_df, use_container_width=True)
            
            if relationships:
                st.markdown("**Relationships**")
                rel_df = pd.DataFrame(relationships)
                st.dataframe(rel_df[['source', 'relation', 'target']], use_container_width=True)
            
            if chunks:
                st.markdown("**Text Units**")
                chunk_data = [{
                    'Chunk ID': c['chunk_id'],
                    'Source': c.get('source_manual', 'Unknown'),
                    'Preview': c['text'][:150] + '...'
                } for c in chunks[:10]]
                st.dataframe(pd.DataFrame(chunk_data), use_container_width=True)

if __name__ == "__main__":
    main()
