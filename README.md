# Healthcare Policy Research Assistant

A GraphRAG-powered chatbot for Medicare coverage policy research, powered by Streamlit.

## 🚀 Live Demo

[Access the app here](https://your-app-name.streamlit.app) (after deployment)

## 📊 Features

- **Dual Search Modes**:
  - Standard Search: Keyword-based text retrieval
  - Relationship Analysis: Graph-based entity exploration
  
- **Knowledge Graph**: 241 entities, 311 relationships from CMS Medicare Coverage Database

- **LLM-Powered Answers**: Using Llama 3.3 70B (via Databricks) or GPT-4 (via OpenAI)

- **Transparent Sources**: Shows entities, relationships, and text chunks for each answer

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## 🔒 Configuration

Create `.streamlit/secrets.toml` with:

```toml
DATABRICKS_TOKEN = "your_token"
DATABRICKS_HOST = "https://your-workspace.cloud.databricks.com"
MODEL_NAME = "databricks-meta-llama-3-3-70b-instruct"
```

## 📁 Data

Knowledge graph data is in the `data/` folder:
- `entities.parquet` (241 entities)
- `relationships.parquet` (311 relationships)
- `text_units.parquet` (318 text chunks)

## 🎓 Example Questions

**Standard Search:**
- What are the lung cancer screening NCD requirements?
- List HCPCS codes for preventive services

**Relationship Analysis:**
- How are Medicare preventive services and screening procedures related?
- What policies affect Medicare beneficiaries?

## 📝 License

Educational/Research Use
