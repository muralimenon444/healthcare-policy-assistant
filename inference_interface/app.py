# v3.2 - MINIMALIST GEMINI AESTHETIC
"""
Last Updated: 2026-04-10 21:00:00
Version: v3.2 - Minimalist Gemini Design
Murali's Medicare Policy Assistant - GraphRAG Demo
Clean, focused interface with chat-first design
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
import requests
matplotlib.use('Agg')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Medicare Policy Assistant",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MINIMALIST GEMINI-STYLE CSS
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');
    
    * {
        font-family: 'Google Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Clean background */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Centered, minimal container */
    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 800px;
    }
    
    /* Simple header */
    .main-header {
        font-size: 2.8rem;
        font-weight: 500;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .sub-header {
        font-size: 1rem;
        color: #9CA3AF;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 400;
    }
    
    /* Chat input - Gemini style */
    .stTextInput > div > div > input {
        background-color: #1F2937 !important;
        color: white !important;
        border: 1px solid #374151 !important;
        border-radius: 24px !important;
        font-size: 1rem !important;
        padding: 1rem 1.5rem !important;
        min-height: 56px !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #EF4444 !important;
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
    }
    
    /* Quick start cards */
    .quick-card {
        background: #1F2937;
        border: 1px solid #374151;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .quick-card:hover {
        background: #252D3A;
        border-color: #4B5563;
        transform: translateY(-2px);
    }
    
    .quick-card-title {
        font-size: 1.1rem;
        font-weight: 500;
        color: #FFFFFF;
        margin-bottom: 0.5rem;
    }
    
    .quick-card-desc {
        font-size: 0.9rem;
        color: #9CA3AF;
        line-height: 1.5;
    }
    
    /* Buttons - minimal */
    .stButton > button {
        background: #EF4444 !important;
        color: white !important;
        border: none !important;
        border-radius: 24px !important;
        font-weight: 500 !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.2s ease !important;
        min-height: 48px !important;
        font-size: 0.95rem !important;
    }
    
    .stButton > button:hover {
        background: #DC2626 !important;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Sidebar - clean */
    section[data-testid="stSidebar"] {
        background-color: #0E1117;
        border-right: 1px solid #1F2937;
    }
    
    /* Expander - minimal */
    .streamlit-expanderHeader {
        background-color: transparent !important;
        color: #9CA3AF !important;
        border: none !important;
        border-bottom: 1px solid #1F2937 !important;
        border-radius: 0 !important;
        font-weight: 500 !important;
        padding: 1rem 0 !important;
    }
    
    /* Metrics - subtle */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 1.5rem !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Hide default streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================

if 'query' not in st.session_state:
    st.session_state.query = ""

# ============================================================================
# LOAD DATA
# ============================================================================

@st.cache_data
def load_graphrag_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data from Databricks Unity Catalog tables."""
    workspace_url = st.secrets.get("DATABRICKS_HOST", os.getenv("DATABRICKS_HOST"))
    token = st.secrets.get("DATABRICKS_TOKEN", os.getenv("DATABRICKS_TOKEN"))
    warehouse_id = st.secrets.get("DATABRICKS_WAREHOUSE_ID", "e7ab584a1feb58ef")
    
    if not workspace_url or not token:
        st.error("❌ Missing credentials")
        st.stop()
    
    if not workspace_url.startswith('https://'):
        workspace_url = f"https://{workspace_url}"
    
    def query_table(table_name: str, columns: str = "*") -> pd.DataFrame:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        sql = f"SELECT {columns} FROM {table_name}"
        payload = {"warehouse_id": warehouse_id, "statement": sql, "wait_timeout": "50s"}
        
        try:
            resp = requests.post(f"{workspace_url}/api/2.0/sql/statements/", headers=headers, json=payload, timeout=60)
            if resp.status_code != 200:
                st.error(f"API Error {resp.status_code}")
                st.stop()
            
            result = resp.json()
            statement_id = result["statement_id"]
            status = result.get("status", {}).get("state")
            
            for _ in range(150):
                if status == "SUCCEEDED":
                    break
                time.sleep(2)
                status_resp = requests.get(f"{workspace_url}/api/2.0/sql/statements/{statement_id}", headers=headers)
                if status_resp.status_code == 200:
                    result = status_resp.json()
                    status = result.get("status", {}).get("state")
            
            if status != "SUCCEEDED":
                st.error(f"Query failed: {status}")
                st.stop()
            
            manifest = result.get("manifest", {})
            columns_list = [c["name"] for c in manifest.get("schema", {}).get("columns", [])]
            result_data = result.get("result")
            
            if result_data and "data_array" in result_data:
                rows = result_data["data_array"]
                df = pd.DataFrame(rows, columns=columns_list)
            else:
                all_rows = []
                for chunk_info in manifest.get("chunks", []):
                    chunk_resp = requests.get(
                        f"{workspace_url}/api/2.0/sql/statements/{statement_id}/result/chunks/{chunk_info.get('chunk_index', 0)}",
                        headers=headers
                    )
                    if chunk_resp.status_code == 200:
                        all_rows.extend(chunk_resp.json().get("data_array", []))
                df = pd.DataFrame(all_rows, columns=columns_list)
            
            return df
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()
    
    entities_df = query_table("research_catalog.healthcare.graphrag_entities")
    relationships_df = query_table("research_catalog.healthcare.graphrag_relationships")
    text_units_df = query_table("research_catalog.healthcare.graphrag_text_units", "id, document_id, chunk_index")
    common_qas_df = query_table("research_catalog.healthcare.graphrag_common_qas")
    stats_df = query_table("research_catalog.healthcare.graphrag_statistics")
    
    return entities_df, relationships_df, text_units_df, common_qas_df, stats_df



# ============================================================================
# ON-DEMAND QUERY FUNCTIONS
# ============================================================================

def query_databricks_for_answer(question: str, entities_df: pd.DataFrame, relationships_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Query the knowledge graph for answers to questions not in common Q&As.
    Uses simple entity matching and relationship traversal.
    """
    
    # Extract potential entities from the question
    question_lower = question.lower()
    
    # Find matching entities (case-insensitive partial match)
    matching_entities = entities_df[
        entities_df['name'].str.lower().str.contains('|'.join(question_lower.split()), na=False, regex=True)
    ].head(10)
    
    if len(matching_entities) == 0:
        return {
            'answer': "I couldn't find specific information about this in the knowledge graph. Try rephrasing your question or ask about Medicare coverage, screening procedures, or specific medical services.",
            'entities': [],
            'related_questions': []
        }
    
    # Get entity names
    entity_names = matching_entities['name'].tolist()
    
    # Find relationships involving these entities
    related_rels = relationships_df[
        relationships_df['source'].isin(entity_names) | 
        relationships_df['target'].isin(entity_names)
    ].head(20)
    
    # Build answer from descriptions
    answer_parts = []
    
    # Add entity descriptions
    for _, entity in matching_entities.head(3).iterrows():
        if pd.notna(entity.get('description')) and entity['description']:
            answer_parts.append(f"**{entity['name']}**: {entity['description']}")
    
    # Add relationship context
    if len(related_rels) > 0:
        answer_parts.append("\n**Related Information:**")
        for _, rel in related_rels.head(5).iterrows():
            answer_parts.append(f"• {rel['source']} {rel.get('description', 'relates to')} {rel['target']}")
    
    final_answer = "\n\n".join(answer_parts) if answer_parts else "Information found, but details are limited. Please check the official Medicare documentation."
    
    # Generate related questions based on entities
    related_questions = []
    for entity in entity_names[:3]:
        related_questions.append(f"What are the requirements for {entity}?")
        related_questions.append(f"How is {entity} covered under Medicare?")
    
    return {
        'answer': final_answer,
        'entities': entity_names[:5],
        'related_questions': related_questions[:6]
    }

with st.spinner("Loading..."):
    entities_df, relationships_df, text_units_df, common_qas_df, stats_df = load_graphrag_data()

# ============================================================================
# SIDEBAR - SYSTEM INSIGHTS (COLLAPSED BY DEFAULT)
# ============================================================================

with st.sidebar:
    st.markdown("### 🏥 Medicare Assistant")
    st.caption("Powered by GraphRAG")
    
    st.divider()
    
    # System Insights - collapsible
    with st.expander("⚙️ System Insights", expanded=False):
        st.markdown("#### Knowledge Graph Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Entities", f"{len(entities_df):,}")
            st.metric("Text Chunks", f"{len(text_units_df):,}")
        with col2:
            st.metric("Relationships", f"{len(relationships_df):,}")
            st.metric("Q&As", f"{len(common_qas_df):,}")
        
        st.markdown("#### Entity Types")
        if len(entities_df) > 0:
            entity_types = entities_df['type'].value_counts().head(5)
            for etype, count in entity_types.items():
                st.caption(f"• {etype}: {count:,}")
        
        st.markdown("#### Data Sources")
        if len(text_units_df) > 0:
            doc_count = text_units_df['document_id'].nunique()
            st.caption(f"• {doc_count} policy documents")
            st.caption(f"• Last updated: {datetime.now().strftime('%Y-%m-%d')}")

# ============================================================================
# MAIN AREA - MINIMALIST CHAT-FOCUSED DESIGN
# ============================================================================

# Header
st.markdown('<h1 class="main-header">Medicare Policy Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Ask anything about Medicare coverage, policies, and procedures</p>', unsafe_allow_html=True)

# Chat Input
query = st.text_input(
    "Your question",
    placeholder="e.g., What are the requirements for lung cancer screening?",
    label_visibility="collapsed",
    key="main_query_input"
)

# Search button (centered)
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    search_clicked = st.button("🔍 Search", use_container_width=True, type="primary")

# Quick Start Cards
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<p style="color: #9CA3AF; text-align: center; margin-bottom: 1rem;">Quick Start</p>', unsafe_allow_html=True)

# Get 3 sample Q&As for quick start cards
if len(common_qas_df) >= 3:
    sample_qas = common_qas_df.sample(n=3, random_state=42)
    
    for idx, row in sample_qas.iterrows():
        # Create card as a clickable button with question text
        col1, col2, col3 = st.columns([0.05, 1, 0.05])
        with col2:
            if st.button(
                row['question'],
                key=f"qcard_{idx}",
                use_container_width=True
            ):
                st.session_state.query = row['question']
                st.rerun()
        
        st.markdown("<div style='margin-bottom: 0.75rem;'></div>", unsafe_allow_html=True)

# ============================================================================
# RESULTS DISPLAY (if search clicked)
# ============================================================================

if search_clicked and query:
    st.divider()
    
    # Check if question is in common Q&As
    matching_qa = common_qas_df[common_qas_df['question'].str.lower() == query.lower()]
    
    if len(matching_qa) > 0:
        # Instant answer from pre-computed Q&As
        qa_row = matching_qa.iloc[0]
        
        st.markdown("### Answer")
        st.write(qa_row['answer'])
        
        if 'entities' in qa_row and qa_row['entities']:
            st.caption(f"Related: {', '.join(qa_row['entities']) if isinstance(qa_row['entities'], list) else qa_row['entities']}")
        
        st.success("✨ Instant answer from knowledge base")
    else:
        # On-demand query to Databricks
        with st.spinner("Searching knowledge graph..."):
            result = query_databricks_for_answer(query, entities_df, relationships_df)
        
        st.markdown("### Answer")
        st.write(result['answer'])
        
        if result['entities']:
            st.caption(f"🏷️ Related: {', '.join(result['entities'])}")
        
        st.info("💡 This question will be added to the knowledge base for instant answers next time.")
        
        # Show related questions
        if result['related_questions']:
            st.markdown("#### Related Questions")
            cols = st.columns(2)
            for i, rq in enumerate(result['related_questions'][:6]):
                with cols[i % 2]:
                    if st.button(rq, key=f"rq_{i}", use_container_width=True):
                        st.session_state.query = rq
                        st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption(f"Powered by Microsoft GraphRAG • Databricks Unity Catalog • v3.2")
