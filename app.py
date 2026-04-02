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
    page_title="Medicare Policy Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
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
    .entity-demographic { background-color: #fce4ec; color: #c2185b; }
    .relation-arrow {
        color: #1f77b4;
        font-weight: bold;
        margin: 0 0.5rem;
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
    
    system_prompt = """You are a Medicare coverage policy expert assistant.
Answer relationship questions using BOTH the knowledge graph relationships AND text passages.
Explain how entities are connected and what policies govern them.
Cite specific relationships and passages."""
    
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
        "Data Source: CMS Medicare Coverage Database",
        "Model: Llama 3.3 70B (Databricks) | GraphRAG Knowledge Base",
        "="*70
    ])
    
    return "\n".join(export_lines)

def main():
    # Header
    st.markdown('<div class="main-header">🏥 Medicare Policy Research Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">GraphRAG-powered search across CMS Medicare Coverage Database</div>', unsafe_allow_html=True)
    
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
            ["Standard Search", "Relationship Analysis"],
            help="Standard: Direct keyword search. Relationship: Graph-based entity connections."
        )
        
        st.divider()
        
        st.subheader("📊 Knowledge Graph Stats")
        st.metric("Entities", len(kg_data["entities"]))
        st.metric("Relationships", len(kg_data["relationships"]))
        st.metric("Text Chunks", len(kg_data["text_units"]))
        
        st.divider()
        
        # Entity Explorer
        with st.expander("🔍 Entity Explorer"):
            entity_types = kg_data["entities"]["type"].unique().tolist()
            selected_type = st.selectbox(
                "Browse by Type",
                entity_types,
                help="Explore entities in the knowledge graph"
            )
            
            entities_of_type = kg_data["entities"][kg_data["entities"]["type"] == selected_type]
            st.caption(f"{len(entities_of_type)} {selected_type} entities")
            
            # Show sample entities
            sample_entities = entities_of_type["text"].head(10).tolist()
            for entity in sample_entities:
                st.text(f"• {entity}")
            
            if len(entities_of_type) > 10:
                with st.expander(f"Show all {len(entities_of_type)} entities"):
                    for entity in entities_of_type["text"].tolist():
                        st.text(f"• {entity}")
        
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
    
    # Main chat interface
    st.header("💬 Ask a Question")
    
    # Check if reloading from history
    default_query = ""
    if 'reload_query' in st.session_state:
        default_query = st.session_state.reload_query
        del st.session_state.reload_query
    
    query = st.text_input(
        "Enter your question:",
        value=default_query,
        placeholder="e.g., What are the requirements for lung cancer screening?",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_button:
        st.rerun()
    
    if search_button and query:
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
