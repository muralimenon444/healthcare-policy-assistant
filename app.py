"""
Last Updated: 2026-04-03 16:35:00
Version: PRODUCTION v2.0
Murali's Medicare Policy Assistant - GraphRAG Demo
Streamlit Cloud → Databricks Backend
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
import networkx as nx
from pyvis.network import Network
import tempfile
import base64

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
# CUSTOM CSS - DARK THEME
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
    
    .sub-header {
        font-size: 1.1rem;
        color: #9CA3AF;
        text-align: center;
        margin-bottom: 2rem;
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
    
    /* Cards */
    .info-card {
        background: linear-gradient(135deg, #1F2937, #111827);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #EF4444, #DC2626);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #DC2626, #B91C1C);
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
        transform: translateY(-2px);
    }
    
    /* Search bar */
    .stTextInput > div > div > input {
        background-color: #1F2937;
        color: white;
        border: 2px solid #374151;
        border-radius: 10px;
        font-size: 1.1rem;
        padding: 0.8rem 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #EF4444;
        box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1F2937;
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #9CA3AF;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #EF4444, #DC2626);
        color: white;
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
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #EF4444;
        font-size: 1.8rem;
    }
    
    /* Question chips */
    .question-chip {
        background: linear-gradient(135deg, #374151, #1F2937);
        border: 1px solid #4B5563;
        color: white;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        margin: 0.3rem;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-block;
        font-size: 0.9rem;
    }
    
    .question-chip:hover {
        background: linear-gradient(135deg, #4B5563, #374151);
        border-color: #EF4444;
        transform: translateY(-2px);
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

# ============================================================================
# MOCK BACKEND FUNCTIONS (Replace with actual Databricks calls)
# ============================================================================

def get_knowledge_graph_stats() -> Dict[str, int]:
    """Get KG statistics from Databricks."""
    return {
        "entities": 241,
        "relationships": 311,
        "text_chunks": 318
    }

def detect_entities(query: str) -> List[Dict[str, Any]]:
    """Mock entity detection."""
    # In production: call Databricks GraphRAG entity extraction
    return [
        {"name": "Medicare Part D", "type": "policy", "score": 0.95},
        {"name": "Prescription Drug Plan", "type": "policy", "score": 0.89},
        {"name": "Centers for Medicare & Medicaid Services", "type": "organization", "score": 0.82}
    ]

def traverse_knowledge_graph(entities: List[Dict]) -> List[Dict[str, Any]]:
    """Mock graph traversal."""
    # In production: call Databricks KG traversal API
    return [
        {
            "origin": "Medicare Part D",
            "relationship": "PROVIDES",
            "target": "Prescription Drug Coverage",
            "source": "medicare_coverage_db_chunk_45.pdf"
        },
        {
            "origin": "Prescription Drug Coverage",
            "relationship": "MANAGED_BY",
            "target": "Part D Plan Sponsors",
            "source": "medicare_coverage_db_chunk_89.pdf"
        },
        {
            "origin": "Part D Plan Sponsors",
            "relationship": "APPROVED_BY",
            "target": "Centers for Medicare & Medicaid Services",
            "source": "cms_regulations_2024.pdf"
        }
    ]

def generate_community_summaries(paths: List[Dict]) -> str:
    """Mock community summary generation."""
    # In production: call LLM with context from graph communities
    return "Community analysis: Medicare Part D forms a central policy hub connecting prescription drug coverage, plan sponsors, and CMS oversight regulations."

def synthesize_answer(query: str, context: Dict) -> Dict[str, Any]:
    """Mock answer synthesis with GraphRAG."""
    # In production: call Databricks Foundation Model API with full context
    return {
        "executive_summary": f"**Medicare Part D** is a prescription drug benefit program administered by CMS through approved private plan sponsors. The program provides outpatient prescription drug coverage to Medicare beneficiaries who choose to enroll. Part D plans must meet specific coverage requirements including catastrophic coverage and are regulated under federal guidelines.",
        
        "detailed_analysis": """
**Policy Structure**: Medicare Part D operates as a public-private partnership where the federal government sets standards and provides subsidies, while private insurance companies deliver the actual coverage through Part D prescription drug plans (PDPs) and Medicare Advantage Prescription Drug plans (MA-PDs).

**Key Requirements**:
- Plans must cover at least 2 drugs per therapeutic category
- Standard benefit includes deductible, initial coverage, coverage gap, and catastrophic coverage
- Low-income subsidies (LIS/Extra Help) available for eligible beneficiaries
- Annual enrollment period: October 15 - December 7

**Regulatory Oversight**: CMS monitors plan performance, approves formularies, and enforces compliance with Part D regulations. Plans must submit bids annually and maintain quality metrics.
        """,
        
        "temporal_metadata": {
            "effective_date": "January 1, 2006",
            "last_updated": "January 1, 2024",
            "policy_version": "Medicare Modernization Act (MMA) 2003 as amended"
        },
        
        "knowledge_gaps": [
            "Specific cost-sharing details for 2026 benefit year",
            "Latest formulary requirements for specialty drugs",
            "Recent policy changes from Inflation Reduction Act implementation"
        ],
        
        "central_nodes": [
            {"entity": "Medicare Part D", "connections": 31, "centrality": 0.89},
            {"entity": "Centers for Medicare & Medicaid Services", "connections": 28, "centrality": 0.82},
            {"entity": "Part D Plan Sponsors", "connections": 19, "centrality": 0.71}
        ],
        
        "supporting_passages": [
            {
                "text": "Medicare Part D provides prescription drug coverage for Medicare beneficiaries. The program is administered through private plans that contract with CMS and must meet federal standards...",
                "source": "medicare_coverage_database_chunk_45.pdf",
                "score": 0.94,
                "full_text": "Medicare Part D provides prescription drug coverage for Medicare beneficiaries. The program is administered through private plans that contract with CMS and must meet federal standards for coverage, cost-sharing, and quality. Plans must cover at least two drugs per therapeutic category and maintain an approved formulary."
            },
            {
                "text": "Part D plan sponsors must submit annual bids to CMS demonstrating their ability to provide the defined standard benefit or actuarially equivalent coverage...",
                "source": "cms_part_d_regulations_2024.pdf",
                "score": 0.88,
                "full_text": "Part D plan sponsors must submit annual bids to CMS demonstrating their ability to provide the defined standard benefit or actuarially equivalent coverage. CMS reviews bids for adequacy and approves plans that meet all regulatory requirements including network pharmacy access and formulary standards."
            },
            {
                "text": "The Low-Income Subsidy (LIS) program provides additional assistance to eligible Part D enrollees, covering premiums, deductibles, and reducing cost-sharing...",
                "source": "medicare_lis_guidelines.pdf",
                "score": 0.85,
                "full_text": "The Low-Income Subsidy (LIS) program provides additional assistance to eligible Part D enrollees, covering premiums, deductibles, and reducing cost-sharing. Eligibility is based on income below 150% of federal poverty level and limited resources. Automatic enrollment occurs for full-benefit dual eligibles."
            }
        ],
        
        "all_relationships": [
            {"entity1": "Medicare Part D", "relation": "PROVIDES", "entity2": "Prescription Drug Coverage"},
            {"entity1": "Medicare Part D", "relation": "ADMINISTERED_BY", "entity2": "Centers for Medicare & Medicaid Services"},
            {"entity1": "Part D Plan Sponsors", "relation": "CONTRACT_WITH", "entity2": "Centers for Medicare & Medicaid Services"},
            {"entity1": "Prescription Drug Plans", "relation": "SUBJECT_TO", "entity2": "Federal Regulations"},
            {"entity1": "Medicare Beneficiaries", "relation": "ENROLL_IN", "entity2": "Part D Plans"},
        ] + [{"entity1": f"Entity_{i}", "relation": "RELATES_TO", "entity2": f"Entity_{i+1}"} for i in range(58)],  # Mock 63 total
        
        "citations": [
            "Medicare Coverage Database - Part D Overview (2024)",
            "42 CFR Part 423 - Prescription Drug Benefit",
            "CMS Part D Policy Manual Chapter 6",
            "Medicare Modernization Act of 2003 (P.L. 108-173)"
        ],
        
        "related_questions": [
            "What are the income eligibility requirements for Part D Low-Income Subsidy?",
            "How do Medicare Advantage plans integrate Part D coverage?",
            "What drugs are excluded from Part D coverage?",
            "How does the Part D coverage gap (donut hole) work in 2026?"
        ]
    }

def run_graphrag_query(query: str, mode: str) -> Dict[str, Any]:
    """
    Main GraphRAG pipeline - orchestrates all steps.
    In production: calls Databricks workspace endpoints.
    """
    # Step 1: Entity detection
    entities = detect_entities(query)
    
    # Step 2: Graph traversal
    paths = traverse_knowledge_graph(entities)
    
    # Step 3: Community summaries
    community_summary = generate_community_summaries(paths)
    
    # Step 4: Answer synthesis
    result = synthesize_answer(query, {
        "entities": entities,
        "paths": paths,
        "community_summary": community_summary
    })
    
    result["entities"] = entities
    result["graph_paths"] = paths
    
    return result

def create_graph_visualization(entities: List[Dict], paths: List[Dict]) -> str:
    """Create interactive graph with pyvis."""
    net = Network(height="600px", width="100%", bgcolor="#0E1117", font_color="white")
    
    # Configure physics
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "stabilization": {"iterations": 200},
            "barnesHut": {"gravitationalConstant": -8000, "springLength": 200}
        },
        "nodes": {
            "font": {"size": 14, "color": "white"},
            "borderWidth": 2,
            "shadow": true
        },
        "edges": {
            "font": {"size": 10, "color": "white", "align": "middle"},
            "arrows": {"to": {"enabled": true}},
            "smooth": {"type": "continuous"}
        }
    }
    """)
    
    # Add nodes
    node_set = set()
    for entity in entities:
        node_set.add(entity["name"])
        color = {"policy": "#3B82F6", "procedure": "#8B5CF6", "organization": "#10B981", "condition": "#F59E0B"}.get(entity["type"], "#6B7280")
        net.add_node(entity["name"], label=entity["name"], color=color, size=30, title=f"Type: {entity['type']}\nScore: {entity['score']:.2f}")
    
    for path in paths:
        node_set.add(path["origin"])
        node_set.add(path["target"])
    
    for node in node_set:
        if not net.get_node(node):
            net.add_node(node, label=node, color="#6B7280", size=20)
    
    # Add edges
    for path in paths:
        net.add_edge(path["origin"], path["target"], label=path["relationship"], title=f"Source: {path['source']}")
    
    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w')
    net.save_graph(tmp.name)
    
    with open(tmp.name, 'r') as f:
        html = f.read()
    
    return html

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def render_entity_pill(entity: Dict):
    """Render colored entity pill."""
    type_class = f"entity-{entity['type']}"
    return f'<span class="entity-pill {type_class}">{entity["name"]} ({entity["score"]:.0%})</span>'

def render_question_chip(question: str, key: str):
    """Render clickable question chip."""
    if st.button(f"💡 {question[:80]}{'...' if len(question) > 80 else ''}", key=key, use_container_width=True):
        st.session_state.query = question
        st.rerun()

def simulate_progress(steps: List[str]):
    """Show progress through GraphRAG steps."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, step in enumerate(steps):
        progress = (i + 1) / len(steps)
        progress_bar.progress(progress)
        status_text.text(f"⚙️ {step}")
        time.sleep(0.8)  # Simulate processing
    
    progress_bar.empty()
    status_text.empty()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/medical-heart.png", width=80)
    st.markdown("### 🏥 Medicare Policy Assistant")
    st.caption("GraphRAG-Powered Research Tool")
    
    st.divider()
    
    # Configuration
    st.markdown("### ⚙️ Configuration")
    search_mode = st.radio(
        "Search Mode",
        ["Relationship Analysis", "Standard Search"],
        index=0,
        key="search_mode_radio"
    )
    st.session_state.search_mode = search_mode
    
    if search_mode == "Relationship Analysis":
        st.info("🔗 Uses graph traversal + community detection")
    else:
        st.info("📄 Traditional semantic search")
    
    st.divider()
    
    # Knowledge Graph Stats
    st.markdown("### 📊 Knowledge Graph Stats")
    stats = get_knowledge_graph_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Entities", stats["entities"])
        st.metric("Relationships", stats["relationships"])
    with col2:
        st.metric("Text Chunks", stats["text_chunks"])
    
    st.divider()
    
    # Example Questions
    st.markdown("### 💡 Example Questions")
    
    examples = [
        "What is Medicare Part D?",
        "How does LDCT screening work?",
        "What preventive services does Medicare cover?",
        "Explain the relationship between CMS and Part D sponsors",
        "What are the coverage rules for DME equipment?",
        "How do Medicare Advantage plans differ from Original Medicare?"
    ]
    
    for i, example in enumerate(examples):
        if st.button(f"• {example}", key=f"example_{i}", use_container_width=True):
            st.session_state.query = example
            st.rerun()

# ============================================================================
# MAIN AREA
# ============================================================================

# Header
st.markdown('<h1 class="main-header">🏥 Murali\'s Medicare Policy Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">GraphRAG-Powered Analysis of CMS Medicare Coverage Database</p>', unsafe_allow_html=True)

# Quick Start - Suggested Questions (only show when no results)
if st.session_state.current_results is None:
    with st.expander("🚀 Quick Start - Suggested Questions", expanded=True):
        tab1, tab2, tab3 = st.tabs(["📋 Simple Retrieval", "🔗 Entity Connections", "🔀 Well-Connected Topics"])
        
        with tab1:
            st.caption("Direct facts from policy documents")
            col1, col2, col3 = st.columns(3)
            with col1:
                render_question_chip("What is Medicare Part D Stand-alone Prescription Drug Plan?", "q1")
            with col2:
                render_question_chip("What is Low Dose Computed Tomography (LDCT)?", "q2")
            with col3:
                render_question_chip("What are medicare-preventive-services?", "q3")
        
        with tab2:
            st.caption("How entities relate to each other")
            col1, col2, col3 = st.columns(3)
            with col1:
                render_question_chip("How is CMS connected to Medicare Part D?", "q4")
            with col2:
                render_question_chip("What is the relationship between Part B and preventive services?", "q5")
            with col3:
                render_question_chip("How do Part D sponsors relate to drug coverage?", "q6")
        
        with tab3:
            st.caption("Multi-entity policy questions")
            col1, col2, col3 = st.columns(3)
            with col1:
                render_question_chip("Tell me about Pelvic Screening Examination coverage", "q7")
            with col2:
                render_question_chip("What is the Inflation Reduction Act Subsidy Amount?", "q8")
            with col3:
                render_question_chip("What do Carriers do in Medicare?", "q9")

# Search Bar (centered and prominent)
st.markdown("---")
search_col1, search_col2, search_col3 = st.columns([1, 3, 1])

with search_col2:
    st.markdown("### 🔍 Ask a Question")
    query = st.text_input(
        "Enter your Medicare policy question",
        value=st.session_state.query,
        placeholder="e.g., How does Medicare Part D prescription drug coverage work?",
        label_visibility="collapsed"
    )
    
    search_button = st.button("🔎 Search", type="primary", use_container_width=True)

# ============================================================================
# SEARCH EXECUTION & RESULTS
# ============================================================================

if search_button and query:
    st.session_state.query = query
    
    # Progress indicator
    with st.spinner(""):
        simulate_progress([
            "Detecting entities in your question...",
            "Traversing knowledge graph...",
            "Generating community summaries...",
            "Synthesizing answer with GraphRAG..."
        ])
    
    # Execute search
    results = run_graphrag_query(query, st.session_state.search_mode)
    st.session_state.current_results = results
    st.session_state.search_history.append({
        "query": query,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": st.session_state.search_mode
    })

# Display results if available
if st.session_state.current_results:
    results = st.session_state.current_results
    
    st.markdown("---")
    st.markdown(f"### 🎯 Results for: *\"{st.session_state.query}\"*")
    
    # ========================================================================
    # TABBED RESULTS LAYOUT
    # ========================================================================
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Summary & Answer",
        "🕸️ Graph View", 
        "🔍 Evidence Trail",
        "📚 Sources & Relationships"
    ])
    
    # ========================================================================
    # TAB 1: SUMMARY & ANSWER
    # ========================================================================
    with tab1:
        # Executive Summary
        st.markdown("#### 📋 Executive Summary")
        st.markdown(f'<div class="info-card">{results["executive_summary"]}</div>', unsafe_allow_html=True)
        
        # Detailed Analysis
        st.markdown("#### 📖 Detailed Analysis")
        st.markdown(f'<div class="info-card">{results["detailed_analysis"]}</div>', unsafe_allow_html=True)
        
        # Temporal Metadata
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📅 Temporal Metadata")
            metadata = results["temporal_metadata"]
            st.markdown(f"""
            - **Effective Date**: {metadata['effective_date']}
            - **Last Updated**: {metadata['last_updated']}
            - **Version**: {metadata['policy_version']}
            """)
        
        with col2:
            st.markdown("#### ⚠️ Knowledge Gaps")
            for gap in results["knowledge_gaps"]:
                st.markdown(f"- {gap}")
        
        # GraphRAG Trace (for transparency)
        with st.expander("🔬 GraphRAG Trace (How this answer was built)"):
            st.markdown("**Entities Detected:**")
            entity_html = " ".join([render_entity_pill(e) for e in results["entities"]])
            st.markdown(entity_html, unsafe_allow_html=True)
            
            st.markdown("**Graph Traversal Steps:**")
            st.dataframe(
                pd.DataFrame(results["graph_paths"]),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown(f"**Central Nodes Used:** {len(results['central_nodes'])} entities analyzed")
    
    # ========================================================================
    # TAB 2: GRAPH VIEW
    # ========================================================================
    with tab2:
        st.markdown("#### 🕸️ Interactive Knowledge Subgraph")
        st.caption("Nodes are colored by entity type. Hover for details. Drag to explore.")
        
        # Generate and display graph
        graph_html = create_graph_visualization(results["entities"], results["graph_paths"])
        st.components.v1.html(graph_html, height=650)
        
        # Central Node Analysis
        st.markdown("#### 🎯 Central Node Analysis")
        central_df = pd.DataFrame(results["central_nodes"])
        
        col1, col2, col3 = st.columns(3)
        for i, row in central_df.iterrows():
            with [col1, col2, col3][i]:
                st.metric(
                    row["entity"],
                    f"{row['connections']} connections",
                    f"Centrality: {row['centrality']:.2f}"
                )
    
    # ========================================================================
    # TAB 3: EVIDENCE TRAIL
    # ========================================================================
    with tab3:
        # Entities Detected
        st.markdown("#### 🏷️ Entities Detected")
        entity_html = " ".join([render_entity_pill(e) for e in results["entities"]])
        st.markdown(entity_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Graph Traversal Path
        st.markdown("#### 🛤️ Graph Traversal Path")
        st.caption("The path GraphRAG followed through the knowledge graph")
        
        paths_df = pd.DataFrame(results["graph_paths"])
        
        # Show first 5, rest in expander
        st.dataframe(
            paths_df.head(5),
            use_container_width=True,
            hide_index=True,
            column_config={
                "origin": "Origin Entity",
                "relationship": "Relationship Type",
                "target": "Target Entity",
                "source": "Source Document"
            }
        )
        
        if len(paths_df) > 5:
            with st.expander(f"📂 View all {len(paths_df)} traversal steps"):
                st.dataframe(paths_df, use_container_width=True, hide_index=True)
    
    # ========================================================================
    # TAB 4: SOURCES & RELATIONSHIPS
    # ========================================================================
    with tab4:
        # Supporting Text Passages
        st.markdown("#### 📄 Supporting Text Passages")
        st.caption("Evidence from source documents (ranked by relevance)")
        
        for i, passage in enumerate(results["supporting_passages"]):
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{passage['source']}**")
                with col2:
                    st.markdown(f"**Score:** {passage['score']:.0%}")
                
                st.markdown(f"_{passage['text']}_")
                
                with st.expander("📖 View full text"):
                    st.markdown(passage['full_text'])
                
                st.markdown("---")
        
        # Knowledge Graph Relationships
        st.markdown(f"#### 🔗 Knowledge Graph Relationships ({len(results['all_relationships'])} found)")
        
        # Show first 10
        rel_df = pd.DataFrame(results["all_relationships"][:10])
        st.dataframe(
            rel_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "entity1": "Entity 1",
                "relation": "Relationship",
                "entity2": "Entity 2"
            }
        )
        
        with st.expander(f"📂 View all {len(results['all_relationships'])} relationships"):
            full_rel_df = pd.DataFrame(results['all_relationships'])
            st.dataframe(full_rel_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Citations
        st.markdown("#### 📚 Citations")
        for i, citation in enumerate(results["citations"], 1):
            st.markdown(f"{i}. {citation}")
    
    # ========================================================================
    # RELATED QUESTIONS (Below tabs)
    # ========================================================================
    st.markdown("---")
    st.markdown("### 💡 Related Questions You Might Ask")
    
    cols = st.columns(2)
    for i, related_q in enumerate(results["related_questions"]):
        with cols[i % 2]:
            render_question_chip(related_q, f"related_{i}")
    
    # ========================================================================
    # EXPORT FUNCTIONALITY
    # ========================================================================
    st.markdown("---")
    export_col1, export_col2, export_col3 = st.columns([2, 1, 2])
    
    with export_col2:
        # Prepare export data
        export_data = {
            "query": st.session_state.query,
            "timestamp": datetime.now().isoformat(),
            "mode": st.session_state.search_mode,
            "results": results
        }
        
        export_json = json.dumps(export_data, indent=2)
        
        st.download_button(
            label="📥 Export Results (JSON)",
            data=export_json,
            file_name=f"medicare_graphrag_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6B7280; padding: 2rem;'>
    <p><strong>Murali's Medicare Policy Assistant</strong> | GraphRAG Demo</p>
    <p>Knowledge Graph: 241 entities • 311 relationships • 318 text chunks</p>
    <p>Backend: Databricks | Data: CMS Medicare Coverage Database</p>
</div>
""", unsafe_allow_html=True)
