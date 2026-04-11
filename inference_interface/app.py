"""
Healthcare Policy Assistant v3.5 - Production Ready
Author: Murali (Engineering & Analytics Manager)

Key Features in v3.5:
1. ✅ Lazy Loading: Instant UI with FAQ pre-cache (no blank screen)
2. ✅ Pre-cached Answers: Quick Start buttons use cached Q&A dictionary
3. ✅ Write-back: Auto-INSERT new answers to graphrag_common_qas table
4. ✅ Optimized Caching: @st.cache_data(ttl=3600) for sub-second queries
5. ✅ Progressive Data Loading: Show UI immediately, load full graph on-demand
"""

import streamlit as st
import pandas as pd
import json
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

# Databricks SQL connection
try:
    from databricks import sql as databricks_sql
except ImportError:
    databricks_sql = None
    st.error("❌ databricks-sql-connector not installed. Run: pip install databricks-sql-connector")

# OpenAI for LLM
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Visualization
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
except ImportError:
    nx = None

# ============================================================================
# CONFIGURATION
# ============================================================================

CATALOG = "research_catalog"
SCHEMA = "healthcare"
ENTITIES_TABLE = f"{CATALOG}.{SCHEMA}.graphrag_entities"
RELATIONSHIPS_TABLE = f"{CATALOG}.{SCHEMA}.graphrag_relationships"
TEXT_UNITS_TABLE = f"{CATALOG}.{SCHEMA}.graphrag_text_units"
COMMON_QAS_TABLE = f"{CATALOG}.{SCHEMA}.graphrag_common_qas"

CACHE_TTL = 3600  # 1 hour cache

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Medicare Policy Assistant v3.5",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MINIMALIST CSS
# ============================================================================

st.markdown("""
<style>
    .main-header {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .quick-start-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.3s;
        text-align: center;
    }
    .quick-start-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        transform: translateY(-2px);
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
</style>
""", unsafe_allow_html=True)

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    def __init__(self, max_requests=15, time_window_minutes=5):
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

rate_limiter = RateLimiter()

def get_client_id():
    if 'client_id' not in st.session_state:
        st.session_state.client_id = str(uuid.uuid4())
    return st.session_state.client_id

def check_rate_limit():
    client_id = get_client_id()
    if not rate_limiter.is_allowed(client_id):
        st.error(f"🚫 Rate limit exceeded! Please wait 5 minutes.")
        st.stop()
    remaining = rate_limiter.get_remaining(client_id)
    if remaining <= 3:
        st.caption(f"⚠️ {remaining} requests remaining")

# ============================================================================
# DATABRICKS SQL CONNECTION
# ============================================================================

@st.cache_resource
def get_databricks_connection():
    """Create Databricks SQL Warehouse connection."""
    try:
        host = st.secrets["DATABRICKS_HOST"]
        token = st.secrets["DATABRICKS_TOKEN"]
        warehouse_id = st.secrets["DATABRICKS_WAREHOUSE_ID"]
        
        connection = databricks_sql.connect(
            server_hostname=host,
            http_path=f"/sql/1.0/warehouses/{warehouse_id}",
            access_token=token
        )
        return connection
    except KeyError as e:
        st.error(f"❌ Missing secret: {e}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        st.stop()

def query_table(sql_query: str) -> pd.DataFrame:
    """Execute SQL query and return DataFrame."""
    try:
        connection = get_databricks_connection()
        cursor = connection.cursor()
        cursor.execute(sql_query)
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=columns)
        cursor.close()
        
        return df
    except Exception as e:
        st.error(f"❌ SQL query failed: {e}")
        return pd.DataFrame()

# ============================================================================
# PHASE 1: QUICK DATA LOADING (Instant UI)
# ============================================================================

@st.cache_data(ttl=CACHE_TTL)
def load_common_qas_quick() -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    PHASE 1 LOADING (Instant):
    Load only common Q&As for immediate UI display.
    Returns: (DataFrame, dict of {question: answer})
    """
    query = f"SELECT * FROM {COMMON_QAS_TABLE}"
    df = query_table(query)
    
    # Create pre-cached dictionary for instant lookups
    faq_dict = {}
    if not df.empty and 'question' in df.columns and 'answer' in df.columns:
        for _, row in df.iterrows():
            question = row['question'].strip().lower()
            answer = row['answer']
            faq_dict[question] = answer
    
    return df, faq_dict

# ============================================================================
# PHASE 2: FULL GRAPH LOADING (On-Demand)
# ============================================================================

@st.cache_data(ttl=CACHE_TTL)
def load_entities():
    """Load entities (cached for 1 hour)."""
    query = f"SELECT * FROM {ENTITIES_TABLE}"
    return query_table(query)

@st.cache_data(ttl=CACHE_TTL)
def load_relationships():
    """Load relationships (cached for 1 hour)."""
    query = f"SELECT * FROM {RELATIONSHIPS_TABLE}"
    return query_table(query)

@st.cache_data(ttl=CACHE_TTL)
def load_text_units():
    """Load text units (cached for 1 hour)."""
    query = f"SELECT * FROM {TEXT_UNITS_TABLE}"
    return query_table(query)

def load_full_graph():
    """
    PHASE 2 LOADING (On-Demand):
    Load full knowledge graph when user performs a search.
    """
    entities_df = load_entities()
    relationships_df = load_relationships()
    text_units_df = load_text_units()
    
    if entities_df.empty or relationships_df.empty or text_units_df.empty:
        st.error("❌ Failed to load knowledge graph data.")
        st.error("Ensure Delta tables exist and are populated.")
        st.stop()
    
    text_col = "text" if "text" in text_units_df.columns else text_units_df.columns[0]
    
    return {
        "entities": entities_df,
        "relationships": relationships_df,
        "text_units": text_units_df,
        "text_column": text_col
    }

# ============================================================================
# WRITE-BACK TO DELTA TABLE
# ============================================================================

def write_back_new_qa(question: str, answer: str, entities: List[str]):
    """
    Write new Q&A back to graphrag_common_qas table.
    This auto-caches on-demand answers for future instant retrieval.
    """
    try:
        connection = get_databricks_connection()
        cursor = connection.cursor()
        
        # Prepare data
        qa_id = str(uuid.uuid4())
        entities_json = json.dumps(entities) if entities else "[]"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # INSERT query
        insert_query = f"""
        INSERT INTO {COMMON_QAS_TABLE} 
        (id, question, answer, entities, last_updated, source)
        VALUES (
            '{qa_id}',
            '{question.replace("'", "''")}',
            '{answer.replace("'", "''")}',
            '{entities_json.replace("'", "''")}',
            TIMESTAMP '{timestamp}',
            'on_demand_graphrag'
        )
        """
        
        cursor.execute(insert_query)
        cursor.close()
        
        # Clear cache so new FAQ is available immediately
        load_common_qas_quick.clear()
        
        return True
    except Exception as e:
        # Silent fail - don't break user experience
        print(f"Write-back failed: {e}")
        return False

# ============================================================================
# LLM CLIENT
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

def search_in_faq_dict(query: str, faq_dict: Dict[str, str]) -> Optional[str]:
    """
    Search in pre-cached FAQ dictionary for instant answer.
    Returns answer if found, None otherwise.
    """
    query_normalized = query.strip().lower()
    
    # Exact match
    if query_normalized in faq_dict:
        return faq_dict[query_normalized]
    
    # Fuzzy match (80% similarity)
    from difflib import SequenceMatcher
    for question, answer in faq_dict.items():
        similarity = SequenceMatcher(None, query_normalized, question).ratio()
        if similarity >= 0.8:
            return answer
    
    return None

def search_text_chunks(query: str, kg_data: Dict, top_k: int = 5) -> List[Dict]:
    """Find relevant text chunks."""
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
        
        overlap = len(query_words & chunk_words)
        score = overlap / max(len(query_words), 1)
        
        if query_lower in chunk_text.lower():
            score += 0.5
        
        if score > 0:
            results.append({
                "chunk_id": idx,
                "text": chunk_text,
                "score": score,
                "document_id": row.get("document_id", "unknown"),
                "source_manual": row.get("source_manual", "Unknown")
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
        
        if entity_lower in query_lower:
            matches.append((entity_text, entity['type'], 1.0))
            continue
        
        overlap = len(entity_words & query_words)
        if overlap > 0:
            score = overlap / max(len(entity_words), len(query_words))
            if score >= threshold:
                matches.append((entity_text, entity['type'], score))
    
    seen = set()
    unique_matches = []
    for match in matches:
        if match[0] not in seen:
            seen.add(match[0])
            unique_matches.append(match)
    
    unique_matches.sort(key=lambda x: x[2], reverse=True)
    return unique_matches[:10]

def find_relationships(entity_names: List[str], kg_data: Dict) -> List[Dict]:
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

def get_chunks_from_relationships(relationships: List[Dict], kg_data: Dict) -> List[Dict]:
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
    """Generate answer using LLM."""
    if not chunks:
        return "No relevant information found.", "No analysis available."
    
    context_parts = ["RELEVANT POLICY EXCERPTS:\n"]
    for i, chunk in enumerate(chunks[:3], 1):
        context_parts.append(f"[Source {i}] ({chunk.get('source_manual', 'Unknown')})\n{chunk['text'][:800]}\n")
    
    if relationships:
        context_parts.append("\nKNOWLEDGE GRAPH RELATIONSHIPS:\n")
        for rel in relationships[:10]:
            context_parts.append(f"- {rel['source']} → {rel['relation']} → {rel['target']}")
    
    context = "\n".join(context_parts)
    
    system_prompt = "You are a Medicare policy expert. Answer using provided excerpts with **[Source N]** citations."
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    
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
        reasoning = generate_reasoning_path(query, entities, relationships, chunks)
        return answer, reasoning
    except Exception as e:
        return f"Error: {e}", "Error in analysis."

def generate_reasoning_path(query: str, entities: List[Tuple], relationships: List[Dict], chunks: List[Dict]) -> str:
    """Generate 3-step reasoning path."""
    steps = []
    
    if entities:
        entity_names = [e[0] for e in entities[:3]]
        steps.append(f"**Step 1:** Identified entities: {', '.join(entity_names)}")
    else:
        steps.append("**Step 1:** Analyzed keywords")
    
    if relationships:
        steps.append(f"**Step 2:** Found {len(relationships)} relationships")
    else:
        steps.append("**Step 2:** Searched documents")
    
    source_manuals = set(c.get('source_manual', 'Unknown') for c in chunks)
    steps.append(f"**Step 3:** Found {len(chunks)} passages from {len(source_manuals)} manual(s)")
    
    return "\n\n".join(steps)

# ============================================================================
# GRAPH VISUALIZATION
# ============================================================================

def create_knowledge_graph_viz(entities: List[Tuple], relationships: List[Dict]) -> plt.Figure:
    """Create NetworkX graph visualization."""
    if nx is None:
        return None
    
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
    
    ax.set_title("Knowledge Graph", fontsize=16, fontweight='bold')
    ax.axis('off')
    plt.tight_layout()
    
    return fig

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # ========================================================================
    # PHASE 1: INSTANT UI (NO LOADING SCREEN)
    # ========================================================================
    
    # Load only FAQs immediately
    qas_df, faq_dict = load_common_qas_quick()
    
    # Initialize session state
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    if 'current_answer' not in st.session_state:
        st.session_state.current_answer = None
    
    # ========================================================================
    # SIDEBAR (Always visible)
    # ========================================================================
    
    with st.sidebar:
        st.markdown("## 🏥 Medicare Policy Assistant")
        st.markdown("### v3.5 Production")
        
        st.markdown("---")
        st.markdown("### 📊 System Status")
        st.metric("Cached FAQs", len(faq_dict))
        
        with st.expander("💡 What's New in v3.5"):
            st.markdown("""
            - ⚡ **Instant UI**: No loading screen
            - 🚀 **Pre-cached Answers**: Sub-second Quick Start
            - 💾 **Auto-Learning**: New answers cached automatically
            - 🔄 **Lazy Loading**: Full graph loaded on-demand
            """)
        
        with st.expander("🛠️ System Info"):
            st.markdown("**Author:** Murali")
            st.markdown("**Engine:** GraphRAG + Llama 3.3")
            st.markdown("**Platform:** Databricks + Streamlit")
    
    # ========================================================================
    # LANDING PAGE (Instant Display)
    # ========================================================================
    
    if not st.session_state.show_results:
        st.markdown('<div class="main-header">🏥 Medicare Policy Assistant</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Instant AI-Powered Policy Intelligence • v3.5</div>', unsafe_allow_html=True)
        
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
        
        # Quick Start Cards (using pre-cached FAQs)
        st.markdown("### ⚡ Quick Start")
        
        if not qas_df.empty and len(qas_df) >= 4:
            col1, col2, col3, col4 = st.columns(4)
            
            quick_start_questions = qas_df.head(4)['question'].tolist()
            
            with col1:
                if st.button("📋 " + quick_start_questions[0][:40] + "...", use_container_width=True, key="qs1"):
                    st.session_state.search_query = quick_start_questions[0]
                    st.session_state.show_results = True
                    st.session_state.current_answer = faq_dict.get(quick_start_questions[0].strip().lower())
                    st.rerun()
            
            with col2:
                if st.button("🔗 " + quick_start_questions[1][:40] + "...", use_container_width=True, key="qs2"):
                    st.session_state.search_query = quick_start_questions[1]
                    st.session_state.show_results = True
                    st.session_state.current_answer = faq_dict.get(quick_start_questions[1].strip().lower())
                    st.rerun()
            
            with col3:
                if st.button("✅ " + quick_start_questions[2][:40] + "...", use_container_width=True, key="qs3"):
                    st.session_state.search_query = quick_start_questions[2]
                    st.session_state.show_results = True
                    st.session_state.current_answer = faq_dict.get(quick_start_questions[2].strip().lower())
                    st.rerun()
            
            with col4:
                if st.button("📊 " + quick_start_questions[3][:40] + "...", use_container_width=True, key="qs4"):
                    st.session_state.search_query = quick_start_questions[3]
                    st.session_state.show_results = True
                    st.session_state.current_answer = faq_dict.get(quick_start_questions[3].strip().lower())
                    st.rerun()
        else:
            st.info("No Quick Start questions available. Run GraphRAG pipeline to populate FAQs.")
        
        if search_clicked and query:
            st.session_state.search_query = query
            st.session_state.show_results = True
            st.session_state.current_answer = None
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
                st.session_state.current_answer = None
                st.rerun()
        with col2:
            st.markdown(f"### 🔍 Results for: *{query}*")
        
        check_rate_limit()
        
        # Check if we have pre-cached answer
        if st.session_state.current_answer:
            # INSTANT ANSWER from pre-cache
            st.success("⚡ **Instant Answer** (from cache)")
            st.markdown(st.session_state.current_answer)
            
        else:
            # Check FAQ dict first
            cached_answer = search_in_faq_dict(query, faq_dict)
            
            if cached_answer:
                # Found in FAQ dict
                st.success("⚡ **Instant Answer** (from FAQ)")
                st.markdown(cached_answer)
            else:
                # ON-DEMAND SEARCH (Load full graph now)
                with st.spinner("🔍 Analyzing your question..."):
                    # PHASE 2: Load full graph only when needed
                    kg_data = load_full_graph()
                    client = initialize_openai_client()
                    
                    if client is None:
                        st.error("Failed to initialize LLM client.")
                        return
                    
                    # Perform GraphRAG search
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
                
                # Display answer
                st.markdown("### 💡 Analysis")
                st.markdown(answer)
                
                # Write-back to cache
                if chunks:  # Only cache if we found relevant content
                    success = write_back_new_qa(query, answer, entity_names)
                    if success:
                        st.caption("✅ Answer cached for future queries")
                
                # Additional tabs
                tab1, tab2, tab3 = st.tabs(["🧭 Reasoning", "🕸️ Graph", "📚 Evidence"])
                
                with tab1:
                    st.markdown(reasoning)
                
                with tab2:
                    if entities and relationships:
                        try:
                            fig = create_knowledge_graph_viz(entities, relationships)
                            if fig:
                                st.pyplot(fig)
                                plt.close(fig)
                        except Exception as e:
                            st.error(f"Visualization error: {e}")
                    else:
                        st.info("No graph relationships found.")
                
                with tab3:
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
                            'Source': c.get('source_manual', 'Unknown'),
                            'Preview': c['text'][:150] + '...'
                        } for c in chunks[:5]]
                        st.dataframe(pd.DataFrame(chunk_data), use_container_width=True)

if __name__ == "__main__":
    main()
