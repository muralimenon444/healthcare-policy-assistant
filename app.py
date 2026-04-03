"""
Healthcare Policy Research Assistant - Databricks App
A GraphRAG-powered chatbot for Medicare coverage policy research.
"""

import streamlit as st
import pandas as pd
import os
import re
from openai import OpenAI
from difflib import SequenceMatcher
from typing import List, Tuple, Dict, Any


# ============================================================================
# RATE LIMITING (Anti-Spam Protection)
# ============================================================================

from collections import defaultdict
from datetime import datetime, timedelta
import hashlib

# Simple in-memory rate limiter
class RateLimiter:
    def __init__(self, max_requests=10, time_window_minutes=5):
        self.max_requests = max_requests
        self.time_window = timedelta(minutes=time_window_minutes)
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier):
        """Check if request is allowed for this identifier (IP or session)."""
        now = datetime.now()
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.time_window
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(now)
            return True
        return False
    
    def get_remaining(self, identifier):
        """Get remaining requests for this identifier."""
        now = datetime.now()
        recent = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.time_window
        ]
        return max(0, self.max_requests - len(recent))

# Initialize rate limiter (10 requests per 5 minutes)
rate_limiter = RateLimiter(max_requests=10, time_window_minutes=5)

def get_client_id():
    """Get a unique identifier for the client (session-based)."""
    # Use Streamlit session state
    if 'client_id' not in st.session_state:
        # Generate unique ID for this session
        import uuid
        st.session_state.client_id = str(uuid.uuid4())
    return st.session_state.client_id

def check_rate_limit():
    """Check if the current user is within rate limits."""
    client_id = get_client_id()
    
    if not rate_limiter.is_allowed(client_id):
        remaining_time = rate_limiter.time_window.total_seconds() / 60
        st.error(f"🚫 Rate limit exceeded! Please wait {remaining_time:.0f} minutes before making more requests.")
        st.stop()
    
    # Show remaining requests
    remaining = rate_limiter.get_remaining(client_id)
    if remaining <= 3:
        st.caption(f"⚠️ {remaining} requests remaining in this 5-minute window")


# Page configuration
st.set_page_config(
    page_title="Murali's Medicare Policy Assistant | GraphRAG Demo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Slick Dark Theme
st.markdown("""
<style>
    /* Import clean system fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Main app background - Charcoal */
    .stApp {
        background-color: #0E0E0E;
    }
    
    /* Main container with subtle glow */
    .main .block-container {
        background-color: #1A1A1A;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 0 30px rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.2);
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
    }
    
    .sub-header {
        font-size: 1rem;
        color: #A0A0A0;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Source boxes */
    .source-box {
        background-color: #1F1F1F;
        border-left: 4px solid #22C55E;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        color: #E0E0E0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    /* Entity tags with dark theme */
    .entity-tag {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        margin: 0.25rem;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }
    
    .entity-policy { 
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: #FFFFFF;
    }
    .entity-procedure { 
        background: linear-gradient(135deg, #7c3aed 0%, #a78bfa 100%);
        color: #FFFFFF;
    }
    .entity-organization { 
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: #FFFFFF;
    }
    .entity-condition { 
        background: linear-gradient(135deg, #ea580c 0%, #fb923c 100%);
        color: #FFFFFF;
    }
    .entity-demographic { 
        background: linear-gradient(135deg, #db2777 0%, #f472b6 100%);
        color: #FFFFFF;
    }
    
    .relation-arrow {
        color: #22C55E;
        font-weight: bold;
        margin: 0 0.5rem;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0E0E0E;
        border-right: 1px solid rgba(34, 197, 94, 0.2);
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: #0E0E0E;
    }
    
    /* Text colors */
    .stMarkdown, p, span, div {
        color: #E0E0E0 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background-color: #1F1F1F !important;
        color: #FFFFFF !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 8px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #22C55E !important;
        box-shadow: 0 0 0 1px #22C55E !important;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: #1F1F1F !important;
        color: #FFFFFF !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 8px !important;
    }
    
    /* Button styling - Gray with White Text */
    .stButton > button {
        background: linear-gradient(135deg, #4B5563 0%, #374151 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #374151 0%, #1F2937 100%) !important;
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #4B5563 0%, #374151 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #374151 0%, #1F2937 100%) !important;
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.3) !important;
    }
    
    /* Form submit button - Primary */
    button[kind="primary"] {
        background: linear-gradient(135deg, #4B5563 0%, #374151 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #374151 0%, #1F2937 100%) !important;
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.3) !important;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        color: #22C55E !important;
        font-weight: 700 !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #A0A0A0 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1F1F1F !important;
        color: #FFFFFF !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 8px !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #22C55E !important;
    }
    
    .streamlit-expanderContent {
        background-color: #1A1A1A !important;
        border: 1px solid #2A2A2A !important;
        color: #E0E0E0 !important;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: #1F1F1F !important;
        border-left: 4px solid #22C55E !important;
        color: #E0E0E0 !important;
    }
    
    .stWarning {
        background-color: #2A1F1A !important;
        border-left: 4px solid #f59e0b !important;
        color: #fbbf24 !important;
    }
    
    .stError {
        background-color: #2A1A1A !important;
        border-left: 4px solid #ef4444 !important;
        color: #fca5a5 !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #22C55E !important;
    }
    
    /* Radio buttons */
    .stRadio > label {
        color: #E0E0E0 !important;
    }
    
    /* Divider */
    hr {
        border-color: #2A2A2A !important;
    }
    
    /* Caption text */
    .stCaption {
        color: #A0A0A0 !important;
    }
    
    /* Links */
    a {
        color: #22C55E !important;
        text-decoration: none !important;
    }
    
    a:hover {
        color: #16a34a !important;
        text-decoration: underline !important;
    }
    
    /* Code blocks */
    code {
        background-color: #1F1F1F !important;
        color: #22C55E !important;
        padding: 0.2rem 0.4rem !important;
        border-radius: 4px !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1A1A1A;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #2A2A2A;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #22C55E;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION & DATA LOADING
# ============================================================================

@st.cache_resource
def initialize_openai_client():
    """Initialize OpenAI client using Streamlit secrets."""
    try:
        # Option 1: Use Databricks (if credentials provided)
        if "DATABRICKS_TOKEN" in st.secrets and "DATABRICKS_HOST" in st.secrets:
            client = OpenAI(
                api_key=st.secrets["DATABRICKS_TOKEN"],
                base_url=f"{st.secrets['DATABRICKS_HOST']}/serving-endpoints"
            )
            return client
        
        # Option 2: Use OpenAI directly (fallback)
        elif "OPENAI_API_KEY" in st.secrets:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            st.warning("⚠️ Using OpenAI API instead of Databricks. Some features may differ.")
            return client
        
        else:
            st.error("❌ Missing API credentials. Please configure secrets in Streamlit Cloud.")
            st.info("""
            Required secrets (add in Streamlit Cloud dashboard):
            - DATABRICKS_TOKEN (your Databricks personal access token)
            - DATABRICKS_HOST (e.g., https://your-workspace.cloud.databricks.com)
            
            OR use OpenAI:
            - OPENAI_API_KEY (your OpenAI API key)
            """)
            return None
    except Exception as e:
        st.error(f"Failed to initialize client: {e}")
        return None

@st.cache_data
def load_knowledge_graph():
    """Load knowledge graph data from Unity Catalog Volumes."""
    output_path = "data"  # Local data folder
    
    try:
        entities_df = pd.read_parquet(f"{output_path}/entities.parquet")
        relationships_df = pd.read_parquet(f"{output_path}/relationships.parquet")
        text_units_df = pd.read_parquet(f"{output_path}/text_units.parquet")
        
        return {
            "entities": entities_df,
            "relationships": relationships_df,
            "text_units": text_units_df,
            "text_column": "text" if "text" in text_units_df.columns else text_units_df.columns[0]
        }
    except FileNotFoundError as e:
        st.error(f"Knowledge graph files not found: {e}")
        return None
    except Exception as e:
        st.error(f"Error loading knowledge graph: {e}")
        return None

# ============================================================================
# TEXT PROCESSING UTILITIES
# ============================================================================

def normalize_text(text: str) -> str:
    """Normalize text for better matching."""
    text = text.lower()
    text = re.sub(r'[-_/]', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def highlight_keywords(text: str, keywords: List[str]) -> str:
    """Highlight keywords in text (case-insensitive)."""
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        text = pattern.sub(f"**{keyword}**", text)
    return text

# ============================================================================
# DIRECT TEXT SEARCH
# ============================================================================

def search_text_chunks(query: str, kg_data: Dict, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Direct search: Find relevant text chunks using keyword matching.
    Returns list of {chunk_id, text, score, document_id}
    """
    if kg_data is None:
        return []
    
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
        
        # Scoring: word overlap + exact phrase match bonus
        overlap = len(query_words & chunk_words)
        score = overlap / max(len(query_words), 1)
        
        # Bonus for exact phrase match
        if query_lower in chunk_text.lower():
            score += 0.5
        
        if score > 0:
            results.append({
                "chunk_id": idx,
                "text": chunk_text,
                "score": score,
                "document_id": row.get("document_id", "unknown")
            })
    
    # Sort by score and return top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

# ============================================================================
# GRAPH-BASED RELATIONSHIP SEARCH
# ============================================================================

def find_entities_in_query(query: str, kg_data: Dict, threshold: float = 0.3) -> List[Tuple[str, str, float]]:
    """
    Find entities mentioned in the query using fuzzy matching.
    Returns list of (entity_text, entity_type, match_score)
    """
    if kg_data is None:
        return []
    
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
        
        # 1. Exact substring match
        if entity_lower in query_lower or query_lower in entity_lower:
            matches.append((entity_text, entity['type'], 1.0))
            continue
        
        # 2. Normalized substring match
        if entity_normalized in query_normalized or query_normalized in entity_normalized:
            matches.append((entity_text, entity['type'], 0.95))
            continue
        
        # 3. Word overlap match
        overlap = len(entity_words & query_words)
        if overlap > 0:
            score = overlap / max(len(entity_words), len(query_words))
            if score >= threshold:
                matches.append((entity_text, entity['type'], score))
                continue
        
        # 4. Partial word matching
        partial_matches = 0
        for entity_word in entity_words:
            for query_word in query_words:
                if len(entity_word) > 3 and len(query_word) > 3:
                    if entity_word in query_word or query_word in entity_word:
                        partial_matches += 1
                        break
        
        if partial_matches > 0:
            score = partial_matches / max(len(entity_words), len(query_words))
            if score >= threshold:
                matches.append((entity_text, entity['type'], score * 0.8))
    
    # Remove duplicates and sort by score
    seen = set()
    unique_matches = []
    for match in matches:
        if match[0] not in seen:
            seen.add(match[0])
            unique_matches.append(match)
    
    unique_matches.sort(key=lambda x: x[2], reverse=True)
    return unique_matches[:10]

def find_relationships(entity_names: List[str], kg_data: Dict) -> List[Dict[str, Any]]:
    """
    Find relationships involving the given entities.
    Returns list of {source, target, relation, chunk_id}
    """
    if kg_data is None:
        return []
    
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
                    "chunk_id": rel['chunk_id']
                })
                break
    
    return relevant_rels

def get_chunks_from_relationships(relationships: List[Dict], kg_data: Dict) -> List[Dict[str, Any]]:
    """Get text chunks that contain the relationships."""
    if not relationships or kg_data is None:
        return []
    
    text_units_df = kg_data["text_units"]
    text_col = kg_data["text_column"]
    
    chunk_ids = set(rel['chunk_id'] for rel in relationships if 'chunk_id' in rel)
    chunks = []
    
    for chunk_id in chunk_ids:
        if chunk_id < len(text_units_df):
            row = text_units_df.iloc[chunk_id]
            chunks.append({
                "chunk_id": chunk_id,
                "text": str(row[text_col]),
                "document_id": row.get("document_id", "unknown")
            })
    
    return chunks

# ============================================================================
# LLM ANSWER GENERATION
# ============================================================================

def generate_answer_direct(query: str, chunks: List[Dict], client: OpenAI) -> str:
    """Generate answer using direct text search results."""
    if not chunks:
        return "No relevant information found in the policy documents."
    
    # Build context from chunks
    context_parts = ["RELEVANT POLICY EXCERPTS:\n"]
    for i, chunk in enumerate(chunks[:3], 1):
        context_parts.append(f"[Excerpt {i}]\n{chunk['text'][:800]}\n")
    
    context = "\n".join(context_parts)
    
    system_prompt = """You are a Medicare coverage policy expert assistant.
Answer questions accurately using ONLY the provided policy excerpts.
Cite specific policies, codes, or requirements when mentioned in the excerpts.
If the excerpts don't contain enough information, say so clearly."""
    
    user_prompt = f"""Context:\n{context}\n\nQuestion: {query}\n\nProvide a clear, accurate answer based on the policy excerpts."""
    
    try:
        response = client.chat.completions.create(
            model=st.secrets.get("MODEL_NAME", "databricks-meta-llama-3-3-70b-instruct"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=600,
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating answer: {e}"

def generate_answer_graph(query: str, entities: List[Tuple], relationships: List[Dict], chunks: List[Dict], client: OpenAI) -> str:
    """Generate answer using graph-based relationship search."""
    if not entities:
        return "No relevant entities found in your question. Try asking about specific policies, procedures, or organizations."
    
    if not relationships:
        return "Found entities but no relationships between them in the knowledge graph."
    
    # Build context
    context_parts = ["KNOWLEDGE GRAPH RELATIONSHIPS:\n"]
    for rel in relationships[:15]:
        context_parts.append(f"- {rel['source']} → {rel['relation']} → {rel['target']}")
    
    context_parts.append("\n\nRELEVANT TEXT PASSAGES:\n")
    for i, chunk in enumerate(chunks[:3], 1):
        context_parts.append(f"[Passage {i}]\n{chunk['text'][:600]}\n")
    
    context = "\n".join(context_parts)
    
    system_prompt = """You are a specialized Medicare Policy Graph Analyst and Research Data Architect for the CMS Medicare Coverage Database.

ROLE: You operate on a Knowledge Graph where data is organized into Entities (Nodes) and Relationships (Edges). Your goal is to provide 100% auditable, visualizable policy research outputs.

═══════════════════════════════════════════════════════════════════════
CORE OBJECTIVE - When answering policy questions:
═══════════════════════════════════════════════════════════════════════

1. IDENTIFY ENTITIES:
   - Extract medical conditions (e.g., Lung Cancer)
   - Extract procedures (e.g., LDCT screening)
   - Extract governing bodies (e.g., USPSTF, CMS)

2. TRAVERSE RELATIONSHIPS:
   - Link conditions to specific National Coverage Determinations (NCDs) or Local Coverage Determinations (LCDs)
   - Use "covered_by", "regulated_by", "requires" relationships
   - Follow the graph structure to find policy connections

3. PRIORITIZE RECENCY:
   - Check effective_date properties on relationship edges
   - If multiple policies exist, highlight the most recent one
   - Note when policies have been updated or superseded

4. EXPLAIN THE PATH:
   - State the chain of logic explicitly
   - Example: "I linked [Condition X] to [Policy Y] because [Organization Z] issued a 'requires' directive on [Date]"
   - Show how you traversed the graph to reach your conclusion

═══════════════════════════════════════════════════════════════════════
RESEARCH VISUALIZATION & TRACEABILITY LAYER:
═══════════════════════════════════════════════════════════════════════

1. VISUAL INFERENCE PATHS (The "Trace"):
   
   For EVERY answer, produce a "Path Summary" table in markdown format:
   
   | Origin Entity | Relationship Type | Target Entity | Source Document |
   |---------------|-------------------|---------------|-----------------|
   | Lung Cancer | covered_by | NCD 210.14 | cms_ncd_210.pdf |
   | NCD 210.14 | requires | USPSTF Grade B | uspstf_2013.pdf |
   
   This allows researchers to visualize the exact graph traversal from question to answer.

2. TEMPORAL METADATA (The "Timeline"):
   
   For every policy entity (NCD/LCD), extract and display:
   - effective_date: When the policy took effect
   - implementation_date: When providers must comply
   - revision_number: Version identifier
   
   If multiple versions exist, FLAG TEMPORAL DRIFT:
   "⏰ TEMPORAL DRIFT DETECTED: This policy was updated on [Date] from [Previous_Version_ID]."

3. KNOWLEDGE GAP DETECTION (The "White Space"):
   
   If an entity from the user's query has ZERO outbound relationships to "Policy" or "Coverage" nodes:
   
   🔍 KNOWLEDGE GAP DETECTED:
   "Entity [X] exists in the database but currently lacks a mapped relationship to a Coverage Determination. 
   This may indicate: (a) Policy not yet indexed, (b) Emerging procedure, or (c) State-level coverage only."

4. CLUSTER DENSITY ANALYSIS (The "Network Hub"):
   
   When summarizing results, identify the "Central Node":
   - The entity with the MOST relationships in the current result set
   - This is the "anchor regulation" for the topic
   
   Example:
   📊 CENTRAL NODE: NCD 210.14 (Lung Cancer Screening)
      - Connected to: 12 entities
      - Hub score: 0.85
      - Interpretation: This is the primary regulatory anchor for lung cancer screening policies.

5. FORMATTING FOR RESEARCH:
   
   At the end of EVERY response, provide a "CITATIONS" block:
   
   ═══════════════════════════════════════════════════════════════════════
   📚 CITATIONS & EVIDENCE TRAIL:
   ═══════════════════════════════════════════════════════════════════════
   
   [1] Entity: Lung Cancer Screening | Relationship: covered_by | Source: NCD 210.14 Section 2.1
   [2] Entity: LDCT Procedure | Relationship: requires | Source: HCPCS G0297 Definition
   [3] Entity: USPSTF Recommendation | Relationship: mandates | Source: Grade B Statement 2013
   
   All HCPCS codes, ICD-10 codes, and technical identifiers must be rendered clearly for technical review.

═══════════════════════════════════════════════════════════════════════
DATA HANDLING PRIORITIES:
═══════════════════════════════════════════════════════════════════════

PRIMARY SOURCE: Knowledge Graph Relationships (entities and edges)
SECONDARY SOURCE: Text Chunks (human-readable evidence for relationships)

If specific parameters (age requirements, pack-years, frequency limits) are missing from text chunks:
- Acknowledge the gap explicitly
- State that the relationship EXISTS in the graph
- Flag as: "⚠️ Parameter details not found in current vector slice"

═══════════════════════════════════════════════════════════════════════
OUTPUT STRUCTURE REQUIREMENTS:
═══════════════════════════════════════════════════════════════════════

1. Executive Summary (2-3 sentences)
2. Graph Traversal Path (markdown table)
3. Detailed Analysis (with temporal metadata if applicable)
4. Knowledge Gaps (if any detected)
5. Central Node Analysis (if multiple entities involved)
6. Citations Block (structured references)

Your goal: Provide accurate, graph-based policy analysis with complete auditability, traceability, and research-grade visualization support."""
    
    user_prompt = f"""Context:\n{context}\n\nQuestion: {query}\n\nExplain the relationships and connections clearly."""
    
    try:
        response = client.chat.completions.create(
            model=st.secrets.get("MODEL_NAME", "databricks-meta-llama-3-3-70b-instruct"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=700,
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating answer: {e}"

# ============================================================================
# UI RENDERING FUNCTIONS
# ============================================================================

def render_entity_tag(entity_text: str, entity_type: str, score: float):
    """Render an entity as a colored tag."""
    st.markdown(
        f'<span class="entity-tag entity-{entity_type}">{entity_text} ({entity_type}) [{score:.2f}]</span>',
        unsafe_allow_html=True
    )

def render_relationship(rel: Dict):
    """Render a relationship triple."""
    st.markdown(
        f"**{rel['source']}** <span class='relation-arrow'>→ {rel['relation']} →</span> **{rel['target']}**",
        unsafe_allow_html=True
    )

def render_text_chunk(chunk: Dict, index: int, query: str):
    """Render a text chunk with highlighting."""
    score = chunk.get('score', 0)
    score_str = f"{score:.2f}" if isinstance(score, (int, float)) else "N/A"
    st.markdown(f"**📄 Source {index + 1}** (Score: {score_str})")
    
    # Highlight query terms
    query_words = query.lower().split()
    highlighted_text = highlight_keywords(chunk['text'][:500], query_words)
    
    st.markdown(f'<div class="source-box">{highlighted_text}...</div>', unsafe_allow_html=True)
    
    with st.expander(f"View full text (Document: {chunk.get('document_id', 'unknown')})"):
        st.text(chunk['text'])

# ============================================================================
# MAIN APPLICATION
# ============================================================================



def generate_related_questions(query: str, entities: List[Tuple], kg_data: Dict, client: OpenAI) -> List[str]:
    """
    Generate related follow-up questions based on the current query and detected entities.
    Returns a list of 3-5 suggested questions.
    """
    try:
        # Build context from entities
        entity_names = [e[0] for e in entities[:5]] if entities else []
        entity_types = [e[1] for e in entities[:5]] if entities else []
        
        # Get a few relationships for context
        relationships = []
        if entity_names and kg_data:
            relationships = find_relationships(entity_names, kg_data)[:5]
        
        # Build prompt for generating related questions
        context_parts = []
        if entity_names:
            context_parts.append(f"Detected entities: {', '.join(entity_names)}")
        if relationships:
            rel_summary = [f"{r['source']} → {r['relation']} → {r['target']}" for r in relationships[:3]]
            context_parts.append(f"Related connections: {'; '.join(rel_summary)}")
        
        context = "\n".join(context_parts) if context_parts else "Medicare policy domain"
        
        prompt = f"""Given this Medicare policy question: "{query}"
        
Context from knowledge graph:
{context}

Generate exactly 3 related follow-up questions that would help the user explore:
1. A deeper dive into the same topic (more specific details)
2. A related policy or procedure connection
3. A practical application or comparison

Format: Return ONLY 3 questions, one per line, no numbering or bullets.
Questions should be natural, specific, and directly related to the original query."""

        response = client.chat.completions.create(
            model=st.secrets.get("MODEL_NAME", "databricks-meta-llama-3-3-70b-instruct"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        
        # Parse response into list of questions
        questions_text = response.choices[0].message.content.strip()
        questions = [q.strip() for q in questions_text.split('\n') if q.strip() and '?' in q]
        
        # Return up to 3 questions
        return questions[:3]
        
    except Exception as e:
        # Fallback to simple entity-based questions if LLM fails
        if entities:
            entity_name = entities[0][0]
            return [
                f"What are the coverage requirements for {entity_name}?",
                f"How does {entity_name} interact with other Medicare policies?",
                f"What are the recent changes to {entity_name} policies?"
            ]
        return []


def create_export_text(query: str, answer: str, sources: List[Dict], mode: str) -> str:
    """Create formatted text for export."""
    export_lines = [
        "="*70,
        "MEDICARE POLICY RESEARCH ASSISTANT - QUERY RESULTS",
        "="*70,
        "",
        f"Query: {query}",
        f"Search Mode: {mode}",
        f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "="*70,
        "ANSWER",
        "="*70,
        "",
        answer,
        "",
        "="*70,
        "SOURCES",
        "="*70,
        ""
    ]
    
    for i, source in enumerate(sources, 1):
        export_lines.append(f"\n[Source {i}]")
        if 'score' in source:
            export_lines.append(f"Relevance Score: {source.get('score', 'N/A')}")
        export_lines.append(f"Document ID: {source.get('document_id', 'unknown')}")
        export_lines.append(f"Text: {source.get('text', '')}\n")
        export_lines.append("-"*70)
    
    export_lines.extend([
        "",
        "="*70,
        "TECHNICAL DETAILS",
        "="*70,
        "",
        "Application: Murali's Medicare Policy Assistant (GraphRAG Demo)",
        "Data Source: CMS Medicare Coverage Database (56 documents)",
        "Knowledge Graph: 241 entities, 311 relationships (built with Microsoft GraphRAG + GPT-4)",
        "Runtime LLM: Llama 3.3 70B Instruct (Databricks Foundation Models)",
        "Built by: Murali Menon",
        "",
        "="*70
    ])
    
    return "\n".join(export_lines)

def main():
    # Header
    st.markdown("<div class='main-header'>🏥 Murali's Medicare Policy Assistant</div>", unsafe_allow_html=True)
    st.markdown('<div class="sub-header">GraphRAG-powered search across CMS Medicare Coverage Database</div>', unsafe_allow_html=True)
    
    # Demo disclaimer and technical info
    with st.expander("ℹ️ About This Project", expanded=False):
        st.markdown("""
        ### 🎓 Educational Demo Project
        
        This application demonstrates the power of **GraphRAG (Graph Retrieval-Augmented Generation)** 
        for intelligent document search and question answering.
        
        ### 🔬 Technical Stack
        
        **Knowledge Graph Generation:**
        - Framework: Microsoft GraphRAG
        - Entity Extraction: GPT-4 (via Azure OpenAI)
        - Documents: 56 CMS Medicare policy documents
        - Output: 241 entities, 311 relationships, 318 text chunks
        
        **Runtime Query Processing:**
        - LLM: Llama 3.3 70B Instruct (Databricks Foundation Models)
        - Serving: Databricks Model Serving Endpoints
        - Search Modes: Direct text search + Graph-based relationship analysis
        
        **Data Source:**
        - CMS Medicare Coverage Database
        - Focus: National Coverage Determinations (NCDs), preventive services, screening procedures
        
        ### 🎯 Purpose
        
        This demo showcases how GraphRAG can:
        - Extract structured knowledge from unstructured policy documents
        - Enable relationship-based queries (not just keyword search)
        - Provide transparent, source-attributed answers
        - Scale to large document collections
        
        ### ⚠️ Disclaimer
        
        This is a **demonstration project** for educational and portfolio purposes. 
        For official Medicare policy guidance, please consult [cms.gov](https://www.cms.gov).
        
        ### 👤 Built By
        
        **Murali Menon**
        
        ---
        
        *Built with Streamlit | Deployed on Streamlit Cloud | Knowledge Base stored in Databricks Unity Catalog*
        """)
    
    # Initialize session state
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'last_result' not in st.session_state:
        st.session_state.last_result = None
    if 'bookmarks' not in st.session_state:
        st.session_state.bookmarks = []
    
    # Initialize
    client = initialize_openai_client()
    kg_data = load_knowledge_graph()
    
    if client is None or kg_data is None:
        st.error("Failed to initialize application. Check configuration and data paths.")
        return
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        search_mode = st.radio(
            "Search Mode",
            ["Relationship Analysis", "Standard Search"],
            help="Relationship: Graph-based entity connections. Standard: Direct keyword search."
        )
        
        st.divider()
        
        st.subheader("📊 Knowledge Graph Stats")
        st.metric("Entities", len(kg_data["entities"]))
        st.metric("Relationships", len(kg_data["relationships"]))
        st.metric("Text Chunks", len(kg_data["text_units"]))
        
        st.divider()

        
        # Search History
        if st.session_state.search_history:
            with st.expander("🕐 Search History"):
                st.caption(f"{len(st.session_state.search_history)} recent queries")
                for i, past_query in enumerate(reversed(st.session_state.search_history[-10:])):
                    if st.button(f"📌 {past_query[:50]}...", key=f"history_{i}"):
                        st.session_state.reload_query = past_query
                        st.rerun()
            
            st.divider()
        
        st.subheader("💡 Example Questions")
        if search_mode == "Standard Search":
            st.markdown("""
            - What are the lung cancer screening requirements?
            - List HCPCS codes for preventive services
            - Describe Medicare prescription drug coverage
            - What are the coverage requirements for LDCT screening?
            """)
        else:
            st.markdown("""
            - How are Medicare preventive services and CMS connected?
            - What policies affect Medicare beneficiaries?
            - How are screening procedures and USPSTF related?
            - What is the National Coverage Determination for lung cancer screening?
            """)
    
    # ============================================================================
    # SUGGESTED QUESTIONS - Quick Start
    # ============================================================================
    
    # Only show suggestions if no query has been made yet
    if not st.session_state.search_history:
        st.markdown("### 🚀 Quick Start - Suggested Questions")
        st.caption("Click any question below to get started")
        
        # Define suggested questions by analysis level
        suggestions = {
            "Simple Retrieval": [
                {
                    "icon": "📋",
                    "question": "What are the coverage requirements for lung cancer screening?",
                    "description": "Direct policy lookup"
                },
                {
                    "icon": "💊",
                    "question": "What is the Medicare Part D prescription drug plan?",
                    "description": "Plan details"
                },
                {
                    "icon": "🏥",
                    "question": "What are Medicare beneficiaries eligible for?",
                    "description": "Eligibility overview"
                }
            ],
            "Entity Connections": [
                {
                    "icon": "🔗",
                    "question": "How does Medicare Part D connect to prescription drug coverage?",
                    "description": "Policy relationships"
                },
                {
                    "icon": "🧬",
                    "question": "What is the relationship between LDCT screening and lung cancer?",
                    "description": "Procedure connections"
                },
                {
                    "icon": "📊",
                    "question": "How do National Coverage Determinations affect local contractors?",
                    "description": "Coverage hierarchy"
                }
            ],
            "Complex Queries": [
                {
                    "icon": "🔀",
                    "question": "What policies affect Medicare Advantage beneficiaries?",
                    "description": "Multi-entity analysis"
                },
                {
                    "icon": "🎯",
                    "question": "What are the out-of-pocket costs for Medicare Part D?",
                    "description": "Cost analysis"
                },
                {
                    "icon": "⚖️",
                    "question": "How do discount programs work with Medicare Part D?",
                    "description": "Program integration"
                }
            ]
        }
        
        # Display suggestions in tabs
        tabs = st.tabs(["📋 Simple Retrieval", "🔗 Entity Connections", "🔀 Complex Queries"])
        
        for tab_idx, (level_name, questions) in enumerate(suggestions.items()):
            with tabs[tab_idx]:
                st.caption(f"**{level_name}:** {'Direct facts from policy documents' if level_name == 'Simple Retrieval' else 'Entity connections and impact' if level_name == 'Relationship Analysis' else 'Multi-source policy integration'}")
                
                # Create 3 columns for the tiles
                cols = st.columns(3)
                
                for idx, suggestion in enumerate(questions):
                    with cols[idx]:
                        # Create a clean card-like button
                        if st.button(
                            f"{suggestion['icon']} **{suggestion['question'][:50]}{'...' if len(suggestion['question']) > 50 else ''}**",
                            key=f"suggest_{level_name}_{idx}",
                            use_container_width=True,
                            help=suggestion['description']
                        ):
                            # Set the query in session state and trigger reload
                            st.session_state.reload_query = suggestion['question']
                            st.rerun()
                        
                        # Add description below button
                        st.caption(f"_{suggestion['description']}_")
        
        st.markdown("---")
    
        # Main chat interface
    st.header("💬 Ask a Question")
    
    # Check if reloading from history
    default_query = ""
    if 'reload_query' in st.session_state and st.session_state.reload_query:
        default_query = st.session_state.reload_query
        # Clear it after using (but only after form submission)
        # Don't delete here - it breaks form submission!
    
    # Use a form so Enter key triggers search
    with st.form(key="search_form", clear_on_submit=False):
        query = st.text_input(
            "Enter your question:",
            value=default_query,
            placeholder="e.g., What are the requirements for lung cancer screening? (Press Enter to search)",
            label_visibility="collapsed"
        )
        
        # Search button (full width, no Clear button needed)
        search_button = st.form_submit_button("🔍 Search", type="primary", use_container_width=True)
    
    if search_button and query:
        # Clear reload_query now that we're searching
        if 'reload_query' in st.session_state:
            st.session_state.reload_query = ""
        
        # Add to search history
        if query not in st.session_state.search_history:
            st.session_state.search_history.append(query)
            # Keep only last 50 queries
            if len(st.session_state.search_history) > 50:
                st.session_state.search_history = st.session_state.search_history[-50:]
        
        # Rate limiting check
        check_rate_limit()
        
        with st.spinner("Analyzing your question..."):
            
            if search_mode == "Standard Search":
                # ============ DIRECT SEARCH MODE ============
                st.subheader("📖 Standard Search Results")
                
                # Search chunks
                chunks = search_text_chunks(query, kg_data, top_k=5)
                
                if chunks:
                    # Generate answer
                    answer = generate_answer_direct(query, chunks, client)
                    
                    # Save to session state
                    st.session_state.last_result = {
                        'query': query,
                        'answer': answer,
                        'sources': chunks,
                        'mode': 'Standard Search'
                    }
                    
                    # Display answer
                    st.markdown("### 💡 Answer")
                    st.info(answer)
                    
                    # Export button
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        export_text = create_export_text(query, answer, chunks, "Standard Search")
                        st.download_button(
                            label="📥 Export",
                            data=export_text,
                            file_name=f"medicare_policy_{query[:30].replace(' ', '_')}.txt",
                            mime="text/plain",
                            help="Download this answer and sources as a text file"
                        )
                    
                    
                    # Display related questions
                    st.markdown("---")
                    st.markdown("### 💡 Related Questions You Might Ask")
                    
                    with st.spinner("Generating related questions..."):
                        # Generate related questions based on query
                        related = generate_related_questions(query, [], kg_data, client)
                        
                        if related:
                            cols = st.columns(len(related))
                            for idx, rel_q in enumerate(related):
                                with cols[idx]:
                                    if st.button(
                                        f"🔍 {rel_q[:60]}{'...' if len(rel_q) > 60 else ''}",
                                        key=f"related_std_{idx}",
                                        use_container_width=True,
                                        help=rel_q
                                    ):
                                        st.session_state.reload_query = rel_q
                                        st.rerun()
                    
                    # Display sources
                    st.markdown("### 📚 Source Text Chunks")
                    st.caption(f"Showing top {len(chunks)} relevant excerpts")
                    
                    for i, chunk in enumerate(chunks):
                        render_text_chunk(chunk, i, query)
                else:
                    st.warning("No relevant text chunks found. Try different keywords.")
            
            else:
                # ============ GRAPH SEARCH MODE ============
                st.subheader("🧠 Relationship Analysis Results")
                
                # Find entities
                entities = find_entities_in_query(query, kg_data, threshold=0.3)
                
                if entities:
                    # Display entities
                    st.markdown("### 🎯 Entities Detected")
                    entity_cols = st.columns(min(len(entities), 5))
                    for i, (text, etype, score) in enumerate(entities[:5]):
                        with entity_cols[i]:
                            render_entity_tag(text, etype, score)
                    
                    # Find relationships
                    entity_names = [e[0] for e in entities]
                    relationships = find_relationships(entity_names, kg_data)
                    
                    if relationships:
                        # Get supporting chunks
                        chunks = get_chunks_from_relationships(relationships, kg_data)
                        
                        # Generate answer
                        answer = generate_answer_graph(query, entities, relationships, chunks, client)
                        
                        # Save to session state
                        st.session_state.last_result = {
                            'query': query,
                            'answer': answer,
                            'sources': chunks,
                            'mode': 'Relationship Analysis'
                        }
                        
                        # Display answer
                        st.markdown("### 💡 Answer")
                        st.info(answer)
                        
                        # Export button
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            export_text = create_export_text(query, answer, chunks, "Relationship Analysis")
                            st.download_button(
                                label="📥 Export",
                                data=export_text,
                                file_name=f"medicare_policy_{query[:30].replace(' ', '_')}.txt",
                                mime="text/plain",
                                help="Download this answer and sources as a text file"
                            )
                        
                        
                        # Display related questions
                        st.markdown("---")
                        st.markdown("### 💡 Related Questions You Might Ask")
                        
                        with st.spinner("Generating related questions..."):
                            # Generate related questions based on query and entities
                            related = generate_related_questions(query, entities, kg_data, client)
                            
                            if related:
                                cols = st.columns(len(related))
                                for idx, rel_q in enumerate(related):
                                    with cols[idx]:
                                        if st.button(
                                            f"🔍 {rel_q[:60]}{'...' if len(rel_q) > 60 else ''}",
                                            key=f"related_graph_{idx}",
                                            use_container_width=True,
                                            help=rel_q
                                        ):
                                            st.session_state.reload_query = rel_q
                                            st.rerun()
                        
                        # Display relationships
                        st.markdown(f"### 🔗 Knowledge Graph Relationships ({len(relationships)} found)")
                        
                        rel_display = st.expander("View all relationships", expanded=True)
                        with rel_display:
                            for rel in relationships[:20]:
                                render_relationship(rel)
                        
                        # Display supporting chunks
                        if chunks:
                            st.markdown(f"### 📚 Supporting Text Passages ({len(chunks)} chunks)")
                            for i, chunk in enumerate(chunks[:3]):
                                render_text_chunk(chunk, i, query)
                    else:
                        st.warning("Found entities but no relationships between them. Try different connection terms.")
                else:
                    st.warning("No entities detected in your question. Try mentioning specific policies, procedures, or organizations.")
    
    # Footer
    st.divider()
    st.caption("🔒 Data Source: CMS Medicare Coverage Database | Model: Llama 3.3 70B | GraphRAG Knowledge Base")

if __name__ == "__main__":
    main()
