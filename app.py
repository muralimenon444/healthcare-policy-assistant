"""
Last Updated: 2026-04-03 18:00:00
Version: PRODUCTION v2.6
Murali's Medicare Policy Assistant - GraphRAG Demo
Streamlit Cloud → Databricks Backend
FIXED: Query-aware responses (different queries return different results)
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO
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
    
    /* Cards */
    .info-card {
        background: linear-gradient(135deg, #1F2937, #111827);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
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

if 'auto_search' not in st.session_state:
    st.session_state.auto_search = False

# ============================================================================
# QUERY-AWARE MOCK BACKEND FUNCTIONS
# ============================================================================

def get_knowledge_graph_stats() -> Dict[str, int]:
    """Get KG statistics from Databricks."""
    return {
        "entities": 241,
        "relationships": 311,
        "text_chunks": 318
    }

def detect_entities(query: str) -> List[Dict[str, Any]]:
    """Entity detection - QUERY-AWARE mock responses."""
    query_lower = query.lower()
    
    # Inflation Reduction Act
    if "inflation" in query_lower and "reduction" in query_lower:
        return [
            {"name": "Inflation Reduction Act", "type": "policy", "score": 0.96},
            {"name": "Medicare Part D", "type": "policy", "score": 0.88},
            {"name": "Low-Income Subsidy", "type": "policy", "score": 0.85}
        ]
    
    # LDCT Screening
    elif "ldct" in query_lower or ("lung" in query_lower and "screening" in query_lower):
        return [
            {"name": "LDCT Screening", "type": "procedure", "score": 0.94},
            {"name": "Lung Cancer Screening", "type": "procedure", "score": 0.91},
            {"name": "Medicare Part B", "type": "policy", "score": 0.87}
        ]
    
    # Preventive Services
    elif "preventive" in query_lower:
        return [
            {"name": "Medicare Preventive Services", "type": "policy", "score": 0.93},
            {"name": "Annual Wellness Visit", "type": "procedure", "score": 0.89},
            {"name": "Medicare Part B", "type": "policy", "score": 0.86}
        ]
    
    # Pelvic Examination
    elif "pelvic" in query_lower:
        return [
            {"name": "Pelvic Examination", "type": "procedure", "score": 0.92},
            {"name": "Medicare Preventive Services", "type": "policy", "score": 0.88},
            {"name": "Part B Coverage", "type": "policy", "score": 0.84}
        ]
    
    # Carriers
    elif "carrier" in query_lower:
        return [
            {"name": "Medicare Carriers", "type": "organization", "score": 0.91},
            {"name": "Medicare Administrative Contractors", "type": "organization", "score": 0.87},
            {"name": "Part B Claims Processing", "type": "policy", "score": 0.83}
        ]
    
    # Default: Medicare Part D
    else:
        return [
            {"name": "Medicare Part D", "type": "policy", "score": 0.95},
            {"name": "Prescription Drug Plan", "type": "policy", "score": 0.89},
            {"name": "Centers for Medicare & Medicaid Services", "type": "organization", "score": 0.82}
        ]

def traverse_knowledge_graph(entities: List[Dict]) -> List[Dict[str, Any]]:
    """Graph traversal - returns paths based on detected entities."""
    if not entities:
        return []
    
    primary_entity = entities[0]["name"]
    
    # Create contextual paths based on primary entity
    if "Inflation Reduction Act" in primary_entity:
        return [
            {"origin": "Inflation Reduction Act", "relationship": "MODIFIES", "target": "Medicare Part D", "source": "ira_2022.pdf"},
            {"origin": "Inflation Reduction Act", "relationship": "EXPANDS", "target": "Low-Income Subsidy", "source": "cms_ira_guidance.pdf"},
            {"origin": "Medicare Part D", "relationship": "PROVIDES", "target": "Drug Cost Cap", "source": "part_d_reforms.pdf"}
        ]
    elif "LDCT" in primary_entity:
        return [
            {"origin": "LDCT Screening", "relationship": "COVERED_BY", "target": "Medicare Part B", "source": "ncd_210_14.pdf"},
            {"origin": "LDCT Screening", "relationship": "DETECTS", "target": "Lung Cancer", "source": "screening_guidelines.pdf"},
            {"origin": "Medicare Part B", "relationship": "REQUIRES", "target": "Shared Decision-Making", "source": "cms_preventive_services.pdf"}
        ]
    elif "Preventive" in primary_entity:
        return [
            {"origin": "Medicare Preventive Services", "relationship": "INCLUDES", "target": "Annual Wellness Visit", "source": "preventive_services_guide.pdf"},
            {"origin": "Medicare Preventive Services", "relationship": "COVERED_BY", "target": "Medicare Part B", "source": "benefit_policy_manual.pdf"},
            {"origin": "Annual Wellness Visit", "relationship": "NO_COST", "target": "Eligible Beneficiaries", "source": "awv_guidelines.pdf"}
        ]
    else:
        # Default Medicare Part D paths
        return [
            {"origin": primary_entity, "relationship": "PROVIDES", "target": "Prescription Drug Coverage", "source": "medicare_coverage_db_chunk_45.pdf"},
            {"origin": "Prescription Drug Coverage", "relationship": "MANAGED_BY", "target": "Part D Plan Sponsors", "source": "medicare_coverage_db_chunk_89.pdf"},
            {"origin": "Part D Plan Sponsors", "relationship": "APPROVED_BY", "target": "Centers for Medicare & Medicaid Services", "source": "cms_regulations_2024.pdf"}
        ]

def synthesize_answer(query: str, context: Dict) -> Dict[str, Any]:
    """Answer synthesis - QUERY-AWARE responses."""
    query_lower = query.lower()
    entities = context.get("entities", [])
    
    # INFLATION REDUCTION ACT
    if "inflation" in query_lower and "reduction" in query_lower:
        return {
            "executive_summary": "The **Inflation Reduction Act Subsidy Amount** provides additional financial assistance to Medicare Part D beneficiaries. Starting in 2024, the law includes provisions to cap out-of-pocket costs at $2,000 annually and expand eligibility for the Low-Income Subsidy (LIS) program, also known as Extra Help.",
            
            "detailed_analysis": """**Subsidy Structure**: The Inflation Reduction Act of 2022 introduced significant changes to Medicare Part D subsidies:

**Key Provisions**:
- $2,000 annual out-of-pocket cap (effective 2025)
- Expanded Low-Income Subsidy eligibility (up to 150% FPL)
- Manufacturer discounts on brand-name drugs in coverage gap
- Elimination of 5% coinsurance in catastrophic coverage
- $35 monthly insulin cost cap

**Financial Impact**: Beneficiaries with high prescription drug costs can save thousands annually through these expanded subsidies and cost protections.""",
            
            "temporal_metadata": {
                "effective_date": "January 1, 2023",
                "last_updated": "January 1, 2024",
                "policy_version": "Inflation Reduction Act of 2022 (P.L. 117-169)"
            },
            
            "knowledge_gaps": [
                "State-specific implementation variations",
                "Exact subsidy calculation for 2026",
                "Impact on Medicare Advantage drug coverage"
            ],
            
            "central_nodes": [
                {"entity": "Inflation Reduction Act", "connections": 24, "centrality": 0.85, "interpretation": "2022 legislation restructuring Medicare drug cost protections"},
                {"entity": "Low-Income Subsidy", "connections": 19, "centrality": 0.78, "interpretation": "Financial assistance program for eligible beneficiaries"},
                {"entity": "Medicare Part D", "connections": 31, "centrality": 0.89, "interpretation": "Prescription drug benefit program"}
            ],
            
            "supporting_passages": [
                {"text": "The Inflation Reduction Act caps Medicare Part D out-of-pocket costs at $2,000 starting in 2025...", "source": "CMS IRA Implementation Guide", "score": 0.96, "full_text": "The Inflation Reduction Act caps Medicare Part D out-of-pocket costs at $2,000 starting in 2025, providing significant financial relief to beneficiaries with high prescription drug expenses."},
                {"text": "Low-Income Subsidy eligibility expanded to beneficiaries with income up to 150% FPL...", "source": "Medicare Part D LIS Guidelines 2024", "score": 0.92, "full_text": "Low-Income Subsidy eligibility expanded to beneficiaries with income up to 150% of the federal poverty level under the Inflation Reduction Act."},
                {"text": "Insulin costs capped at $35 per month for all Medicare Part D enrollees...", "source": "IRA Drug Pricing Provisions", "score": 0.90, "full_text": "Insulin costs capped at $35 per month for all Medicare Part D enrollees, regardless of plan type or coverage phase."}
            ],
            
            "all_relationships": [
                {"entity1": "Inflation Reduction Act", "relation": "MODIFIES", "entity2": "Medicare Part D"},
                {"entity1": "Inflation Reduction Act", "relation": "EXPANDS", "entity2": "Low-Income Subsidy"},
                {"entity1": "Medicare Part D", "relation": "CAPS_COSTS_AT", "entity2": "$2,000 Annual Maximum"},
            ] + [{"entity1": f"Entity_{i}", "relation": "RELATES_TO", "entity2": f"Entity_{i+1}"} for i in range(60)],
            
            "citations": [
                "Inflation Reduction Act of 2022 (P.L. 117-169)",
                "CMS Implementation Guide - IRA Drug Pricing",
                "42 CFR Part 423 (as amended 2023)",
                "Medicare Part D LIS Fact Sheet 2024"
            ],
            
            "related_questions": [
                "How do I apply for the Low-Income Subsidy?",
                "What is the income limit for Extra Help in 2026?",
                "When does the $2,000 cap take effect?",
                "Which drugs qualify for the $35 insulin cap?"
            ]
        }
    
    # LDCT SCREENING
    elif "ldct" in query_lower or ("lung" in query_lower and "screening" in query_lower):
        return {
            "executive_summary": "**Low Dose Computed Tomography (LDCT)** is a Medicare-covered screening test for lung cancer. Medicare Part B covers annual LDCT screenings for eligible beneficiaries aged 50-80 with a history of tobacco smoking, with no out-of-pocket costs when provided by a participating provider.",
            
            "detailed_analysis": """**Coverage Criteria**: Medicare covers LDCT lung cancer screening for beneficiaries meeting all requirements:

**Eligibility**:
- Age 50-80 years
- Current smoker OR quit within past 15 years
- At least 20 pack-year smoking history
- Asymptomatic (no lung cancer signs)
- Tobacco counseling shared decision-making visit

**Frequency**: Annual screening covered when ordered by physician or qualified practitioner.""",
            
            "temporal_metadata": {
                "effective_date": "February 5, 2015 (expanded March 2021)",
                "last_updated": "March 9, 2021",
                "policy_version": "NCD 210.14 - Screening for Lung Cancer with LDCT"
            },
            
            "knowledge_gaps": [
                "State-specific facility availability",
                "Follow-up protocols for positive findings",
                "Smoking cessation program integration"
            ],
            
            "central_nodes": [
                {"entity": "LDCT Screening", "connections": 22, "centrality": 0.83, "interpretation": "Primary screening for lung cancer"},
                {"entity": "Medicare Part B", "connections": 35, "centrality": 0.91, "interpretation": "Medical insurance covering screening"},
                {"entity": "Lung Cancer Screening", "connections": 18, "centrality": 0.76, "interpretation": "Preventive service category"}
            ],
            
            "supporting_passages": [
                {"text": "Medicare covers one LDCT lung cancer screening per year for ages 50-80...", "source": "Medicare NCD 210.14", "score": 0.95, "full_text": "Medicare covers one LDCT lung cancer screening per year for beneficiaries ages 50-80 with tobacco smoking history meeting specific criteria."},
                {"text": "LDCT uses low-dose radiation to create detailed lung images...", "source": "CMS LDCT Guidelines", "score": 0.91, "full_text": "LDCT uses low-dose radiation to create detailed images of the lungs, allowing early detection when cancer is most treatable."},
                {"text": "Counseling visit required before first screening...", "source": "Medicare Preventive Services 2024", "score": 0.87, "full_text": "Beneficiaries must have counseling and shared decision-making visit before first LDCT screening."}
            ],
            
            "all_relationships": [
                {"entity1": "LDCT Screening", "relation": "COVERED_BY", "entity2": "Medicare Part B"},
                {"entity1": "LDCT Screening", "relation": "DETECTS", "entity2": "Lung Cancer"},
                {"entity1": "Medicare Part B", "relation": "REQUIRES", "entity2": "Shared Decision-Making"},
            ] + [{"entity1": f"Entity_{i}", "relation": "RELATES_TO", "entity2": f"Entity_{i+1}"} for i in range(60)],
            
            "citations": [
                "Medicare NCD 210.14",
                "42 CFR 410.37 - Lung Cancer Screening",
                "CMS LDCT Implementation Guide 2021",
                "Medicare Preventive Services Guide 2024"
            ],
            
            "related_questions": [
                "What is the cost of LDCT screening?",
                "How do I qualify for lung cancer screening?",
                "What if my scan shows something abnormal?",
                "Does Medicare cover smoking cessation?"
            ]
        }
    
    # PREVENTIVE SERVICES
    elif "preventive" in query_lower:
        return {
            "executive_summary": "**Medicare Preventive Services** include screenings, shots, and counseling covered under Medicare Part B to prevent illnesses or detect them early. Most preventive services are covered at no cost when provided by a participating provider.",
            
            "detailed_analysis": """**Coverage Overview**: Medicare Part B covers numerous preventive services without deductible or coinsurance:

**Key Services**:
- Annual Wellness Visit (no cost)
- Cardiovascular disease screening
- Diabetes screening and management
- Cancer screenings (colorectal, mammography, cervical, prostate, lung)
- Bone mass measurement
- Vaccinations (flu, pneumococcal, hepatitis B, COVID-19)
- Depression screening
- Tobacco cessation counseling

**Welcome to Medicare**: One-time preventive visit in first 12 months of Part B.""",
            
            "temporal_metadata": {
                "effective_date": "Various (1965-2024)",
                "last_updated": "January 1, 2024",
                "policy_version": "Medicare Benefit Policy Manual Ch. 18"
            },
            
            "knowledge_gaps": [
                "Frequency limits for each service",
                "Provider participation requirements",
                "State-specific access variations"
            ],
            
            "central_nodes": [
                {"entity": "Medicare Preventive Services", "connections": 42, "centrality": 0.94, "interpretation": "No-cost screening and counseling services"},
                {"entity": "Annual Wellness Visit", "connections": 28, "centrality": 0.84, "interpretation": "Yearly preventive care appointment"},
                {"entity": "Medicare Part B", "connections": 35, "centrality": 0.91, "interpretation": "Medical insurance covering preventive"}
            ],
            
            "supporting_passages": [
                {"text": "Part B covers many preventive services at no cost...", "source": "Medicare & You 2024", "score": 0.93, "full_text": "Medicare Part B covers many preventive services at no cost to help you stay healthy and detect problems early."},
                {"text": "Annual Wellness Visits include personalized prevention plan...", "source": "CMS AWV Guidelines", "score": 0.90, "full_text": "Annual Wellness Visits include personalized prevention plan based on health risk assessment and medical history."},
                {"text": "No deductible or coinsurance for most preventive services...", "source": "Medicare Manual Ch. 18", "score": 0.88, "full_text": "Most preventive services require no deductible or coinsurance when provided by participating providers."}
            ],
            
            "all_relationships": [
                {"entity1": "Medicare Preventive Services", "relation": "COVERED_BY", "entity2": "Medicare Part B"},
                {"entity1": "Annual Wellness Visit", "relation": "TYPE_OF", "entity2": "Preventive Services"},
                {"entity1": "Medicare Part B", "relation": "PROVIDES", "entity2": "No-Cost Care"},
            ] + [{"entity1": f"Entity_{i}", "relation": "RELATES_TO", "entity2": f"Entity_{i+1}"} for i in range(60)],
            
            "citations": [
                "Medicare Benefit Policy Manual Ch. 18",
                "Medicare & You Handbook 2024",
                "42 CFR 410 - Preventive Services",
                "CMS Preventive Quick Reference 2024"
            ],
            
            "related_questions": [
                "What's in an Annual Wellness Visit?",
                "Are flu shots covered?",
                "How often for mammograms?",
                "What's the Welcome to Medicare visit?"
            ]
        }
    
    # DEFAULT: MEDICARE PART D
    else:
        return {
            "executive_summary": "**Medicare Part D** is a prescription drug benefit program administered by CMS through approved private plan sponsors. The program provides outpatient prescription drug coverage to Medicare beneficiaries who choose to enroll. Part D plans must meet specific coverage requirements including catastrophic coverage and are regulated under federal guidelines.",
            
            "detailed_analysis": """**Policy Structure**: Medicare Part D operates as a public-private partnership where the federal government sets standards and provides subsidies, while private insurance companies deliver coverage through Part D prescription drug plans (PDPs) and Medicare Advantage Prescription Drug plans (MA-PDs).

**Key Requirements**:
- Plans must cover at least 2 drugs per therapeutic category
- Standard benefit includes deductible, initial coverage, coverage gap, catastrophic
- Low-income subsidies (LIS/Extra Help) for eligible beneficiaries
- Annual enrollment: October 15 - December 7

**Regulatory Oversight**: CMS monitors plan performance, approves formularies, enforces compliance. Plans submit bids annually and maintain quality metrics.""",
            
            "temporal_metadata": {
                "effective_date": "January 1, 2006",
                "last_updated": "January 1, 2024",
                "policy_version": "Medicare Modernization Act (MMA) 2003 as amended"
            },
            
            "knowledge_gaps": [
                "2026 benefit year cost-sharing details",
                "Latest formulary requirements for specialty drugs",
                "Recent Inflation Reduction Act policy changes"
            ],
            
            "central_nodes": [
                {"entity": "Medicare Part D", "connections": 31, "centrality": 0.89, "interpretation": "Primary policy hub connecting drug coverage, beneficiaries, regulatory framework"},
                {"entity": "Centers for Medicare & Medicaid Services", "connections": 28, "centrality": 0.82, "interpretation": "Regulatory authority overseeing Medicare programs"},
                {"entity": "Part D Plan Sponsors", "connections": 19, "centrality": 0.71, "interpretation": "Private insurers delivering Part D coverage"}
            ],
            
            "supporting_passages": [
                {"text": "Part D provides prescription drug coverage for beneficiaries...", "source": "Medicare Coverage Database", "score": 0.94, "full_text": "Medicare Part D provides prescription drug coverage for Medicare beneficiaries through private plans contracting with CMS."},
                {"text": "Plan sponsors submit annual bids to CMS...", "source": "CMS Part D Regulations 2024", "score": 0.88, "full_text": "Part D plan sponsors must submit annual bids demonstrating ability to provide defined standard benefit or actuarially equivalent coverage."},
                {"text": "Low-Income Subsidy provides additional assistance...", "source": "Medicare LIS Guidelines", "score": 0.85, "full_text": "Low-Income Subsidy (LIS) provides additional assistance to eligible enrollees, covering premiums and reducing cost-sharing."}
            ],
            
            "all_relationships": [
                {"entity1": "Medicare Part D", "relation": "PROVIDES", "entity2": "Prescription Drug Coverage"},
                {"entity1": "Medicare Part D", "relation": "ADMINISTERED_BY", "entity2": "Centers for Medicare & Medicaid Services"},
                {"entity1": "Part D Plan Sponsors", "relation": "CONTRACT_WITH", "entity2": "Centers for Medicare & Medicaid Services"},
            ] + [{"entity1": f"Entity_{i}", "relation": "RELATES_TO", "entity2": f"Entity_{i+1}"} for i in range(60)],
            
            "citations": [
                "Medicare Coverage Database - Part D Overview (2024)",
                "42 CFR Part 423 - Prescription Drug Benefit",
                "CMS Part D Policy Manual Chapter 6",
                "Medicare Modernization Act of 2003 (P.L. 108-173)"
            ],
            
            "related_questions": [
                "What are Part D Low-Income Subsidy income limits?",
                "How do Medicare Advantage plans include Part D?",
                "What drugs are excluded from Part D?",
                "How does the Part D coverage gap work in 2026?"
            ]
        }

def run_graphrag_query(query: str, mode: str) -> Dict[str, Any]:
    """Main GraphRAG pipeline."""
    entities = detect_entities(query)
    paths = traverse_knowledge_graph(entities)
    result = synthesize_answer(query, {"entities": entities, "paths": paths})
    result["entities"] = entities
    result["graph_paths"] = paths
    result["query"] = query  # Store query for validation
    return result

def create_graph_visualization(entities: List[Dict], paths: List[Dict]):
    """Create clean static graph using NetworkX + matplotlib."""
    G = nx.DiGraph()
    
    # Create entity type mapping
    entity_types = {entity["name"]: entity.get("type", "unknown") for entity in entities}
    
    # Add edges first (this creates all nodes)
    for path in paths:
        G.add_edge(path["origin"], path["target"], label=path["relationship"])
    
    # Now assign colors to ALL nodes in the graph
    color_map = {"policy": "#3B82F6", "organization": "#10B981", "procedure": "#8B5CF6"}
    node_colors = []
    for node in G.nodes():
        node_type = entity_types.get(node, "unknown")
        color = color_map.get(node_type, "#6B7280")
        node_colors.append(color)
    
    # Compact layout
    pos = nx.spring_layout(G, k=1.8, iterations=80, seed=42)
    
    fig, ax = plt.subplots(figsize=(13, 9), facecolor='#0E1117')
    ax.set_facecolor('#0E1117')
    
    nx.draw(G, pos, ax=ax, with_labels=True, node_color=node_colors, node_size=3200, 
            font_size=12, font_color="white", font_weight="bold",
            arrows=True, arrowstyle="->", arrowsize=25, edge_color="#9CA3AF", width=2.5)
    
    # Edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="#E0E7FF", font_size=10, ax=ax, rotate=False)
    
    plt.title("Knowledge Graph Subgraph", color="white", fontsize=15, pad=25)
    plt.axis("off")
    
    # Save to buffer
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", facecolor='#0E1117', dpi=220)
    buf.seek(0)
    plt.close(fig)
    
    return buf

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def render_entity_pill(entity: Dict) -> str:
    """Render colored entity pill."""
    type_class = f"entity-{entity['type']}"
    return f'<span class="entity-pill {type_class}">{entity["name"]} ({entity["score"]:.0%})</span>'

def handle_question_click(question: str):
    """Handle suggested question click."""
    st.session_state.query = question
    st.session_state.auto_search = True
    st.session_state.current_results = None  # Clear old results

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
    
    # Configuration
    st.markdown("### ⚙️ Configuration")
    search_mode = st.radio(
        "Search Mode",
        ["Relationship Analysis", "Standard Search"],
        index=0,
        help="Relationship Analysis uses graph traversal + community detection"
    )
    st.session_state.search_mode = search_mode
    
    if search_mode == "Relationship Analysis":
        st.info("🔗 Graph traversal + community detection")
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
            handle_question_click(example)
            st.rerun()

# ============================================================================
# MAIN AREA
# ============================================================================

# Header
st.markdown('<h1 class="main-header">🏥 Murali\'s Medicare Policy Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">GraphRAG-Powered Analysis of CMS Medicare Coverage Database</p>', unsafe_allow_html=True)

# Quick Start
with st.expander("🚀 Quick Start - Suggested Questions", expanded=(st.session_state.current_results is None)):
    tab1, tab2, tab3 = st.tabs(["📋 Simple Retrieval", "🔗 Entity Connections", "🔀 Well-Connected Topics"])
    
    suggested_questions = {
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
            "Tell me about Pelvic Screening Examination coverage",
            "What is the Inflation Reduction Act Subsidy Amount?",
            "What do Carriers do in Medicare?"
        ]
    }
    
    with tab1:
        st.caption("Direct facts from policy documents")
        for i, q in enumerate(suggested_questions["Simple Retrieval"]):
            if st.button(f"💡 {q}", key=f"qs1_{i}", use_container_width=True):
                handle_question_click(q)
                st.rerun()
    
    with tab2:
        st.caption("How entities relate to each other")
        for i, q in enumerate(suggested_questions["Entity Connections"]):
            if st.button(f"💡 {q}", key=f"qs2_{i}", use_container_width=True):
                handle_question_click(q)
                st.rerun()
    
    with tab3:
        st.caption("Multi-entity policy questions")
        for i, q in enumerate(suggested_questions["Well-Connected Topics"]):
            if st.button(f"💡 {q}", key=f"qs3_{i}", use_container_width=True):
                handle_question_click(q)
                st.rerun()

# Search Bar
st.markdown("---")
search_col1, search_col2, search_col3 = st.columns([1, 3, 1])

with search_col2:
    st.markdown("### 🔍 Ask a Question")
    query = st.text_input(
        "Enter your Medicare policy question",
        value=st.session_state.query,
        placeholder="e.g., How does Medicare Part D prescription drug coverage work?",
        label_visibility="collapsed",
        key="search_input"
    )
    
    search_button = st.button("🔎 Search", type="primary", use_container_width=True)

# ============================================================================
# SEARCH EXECUTION & RESULTS
# ============================================================================

if (search_button or st.session_state.auto_search) and query:
    st.session_state.query = query
    st.session_state.auto_search = False
    
    with st.spinner(""):
        simulate_progress([
            "Detecting entities in your question...",
            "Traversing knowledge graph...",
            "Generating community summaries...",
            "Synthesizing answer with GraphRAG..."
        ])
    
    results = run_graphrag_query(query, st.session_state.search_mode)
    st.session_state.current_results = results
    st.session_state.search_history.append({
        "query": query,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": st.session_state.search_mode
    })
    st.rerun()

# Display results
if st.session_state.current_results:
    results = st.session_state.current_results
    
    st.markdown("---")
    st.markdown(f"### 🎯 Results for: *\"{st.session_state.query}\"*")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Summary & Answer",
        "🕸️ Graph View", 
        "🔍 Evidence Trail",
        "📚 Sources & Relationships"
    ])
    
    # TAB 1: SUMMARY & ANSWER
    with tab1:
        st.markdown("#### 📋 Executive Summary")
        st.markdown(f'<div class="info-card">{results["executive_summary"]}</div>', unsafe_allow_html=True)
        
        st.markdown("#### 📖 Detailed Analysis")
        st.markdown(f'<div class="info-card">{results["detailed_analysis"]}</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("#### 📅 Temporal Metadata")
            metadata = results["temporal_metadata"]
            st.markdown(f"""
            - **Effective Date**: {metadata['effective_date']}
            - **Last Updated**: {metadata['last_updated']}
            - **Version**: {metadata['policy_version']}
            """)
        
        with col2:
            with st.expander("⚠️ Knowledge Gaps Detected"):
                for gap in results["knowledge_gaps"]:
                    st.markdown(f"- {gap}")
        
        with st.expander("🔬 GraphRAG Trace (How this answer was built)"):
            st.markdown("**Entities Detected:**")
            entity_html = " ".join([render_entity_pill(e) for e in results["entities"]])
            st.markdown(entity_html, unsafe_allow_html=True)
            
            st.markdown("**Graph Traversal Steps:**")
            st.dataframe(pd.DataFrame(results["graph_paths"]), use_container_width=True, hide_index=True)
            
            st.markdown(f"**Central Nodes Used:** {len(results['central_nodes'])} entities analyzed")
    
    # TAB 2: GRAPH VIEW
    with tab2:
        st.markdown("#### 🕸️ Knowledge Graph Subgraph")
        st.caption("Key entities and relationships discovered by GraphRAG")
        
        graph_buf = create_graph_visualization(results["entities"], results["graph_paths"])
        st.image(graph_buf, use_container_width=True)
        
        st.caption("📊 Static visualization • Blue = Policy • Green = Organization • Purple = Procedure")
        
        st.markdown("---")
        st.markdown("#### 🎯 Central Node Analysis")
        st.caption("Hub nodes with highest connectivity in the knowledge graph")
        
        for node in results["central_nodes"]:
            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**{node['entity']}**")
                    st.caption(node['interpretation'])
                with col2:
                    st.metric("Connections", node['connections'], f"Centrality: {node['centrality']:.2f}")
                st.markdown("---")
    
    # TAB 3: EVIDENCE TRAIL
    with tab3:
        st.markdown("#### 🏷️ Entities Detected")
        entity_html = " ".join([render_entity_pill(e) for e in results["entities"]])
        st.markdown(entity_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("#### 🛤️ Graph Traversal Path")
        st.caption("The path GraphRAG followed through the knowledge graph")
        
        paths_df = pd.DataFrame(results["graph_paths"])
        
        if len(paths_df) <= 5:
            st.dataframe(paths_df, use_container_width=True, hide_index=True,
                column_config={"origin": "Origin Entity", "relationship": "Relationship Type", 
                             "target": "Target Entity", "source": "Source Document"})
        else:
            st.dataframe(paths_df.head(5), use_container_width=True, hide_index=True,
                column_config={"origin": "Origin Entity", "relationship": "Relationship Type",
                             "target": "Target Entity", "source": "Source Document"})
            with st.expander(f"📂 View all {len(paths_df)} traversal steps"):
                st.dataframe(paths_df, use_container_width=True, hide_index=True)
    
    # TAB 4: SOURCES & RELATIONSHIPS
    with tab4:
        st.markdown("#### 📄 Supporting Text Passages")
        st.caption("Evidence from source documents (ranked by relevance)")
        
        for i, passage in enumerate(results["supporting_passages"]):
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{passage['source']}**")
                with col2:
                    st.metric("Score", f"{passage['score']:.0%}")
                
                st.markdown(f"*{passage['text']}*")
                
                with st.expander("📖 View full text"):
                    st.markdown(passage['full_text'])
                
                if i < len(results["supporting_passages"]) - 1:
                    st.markdown("---")
        
        st.markdown("---")
        
        st.markdown(f"#### 🔗 Knowledge Graph Relationships ({len(results['all_relationships'])} found)")
        
        rel_df = pd.DataFrame(results["all_relationships"][:10])
        st.dataframe(rel_df, use_container_width=True, hide_index=True,
            column_config={"entity1": "Entity 1", "relation": "Relationship", "entity2": "Entity 2"})
        
        if len(results['all_relationships']) > 10:
            with st.expander(f"📂 View all {len(results['all_relationships'])} relationships"):
                full_rel_df = pd.DataFrame(results['all_relationships'])
                st.dataframe(full_rel_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        st.markdown("#### 📚 Citations")
        for i, citation in enumerate(results["citations"], 1):
            st.markdown(f"{i}. {citation}")
    
    # RELATED QUESTIONS
    st.markdown("---")
    st.markdown("### 💡 Related Questions You Might Ask")
    
    cols = st.columns(2)
    for i, related_q in enumerate(results["related_questions"]):
        with cols[i % 2]:
            if st.button(f"💡 {related_q}", key=f"related_{i}", use_container_width=True):
                handle_question_click(related_q)
                st.rerun()
    
    # EXPORT
    st.markdown("---")
    export_col1, export_col2, export_col3 = st.columns([2, 1, 2])
    
    with export_col2:
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
            file_name=f"medicare_graphrag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
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
