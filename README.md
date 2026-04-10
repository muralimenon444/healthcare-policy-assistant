# Healthcare Policy Assistant: GraphRAG Intelligence

## Project Overview
The Healthcare Policy Assistant is a production-grade AI system designed for high-precision retrieval and analysis of complex CMS Medicare policy documentation. Utilizing **GraphRAG** (Graph-based Retrieval Augmented Generation), the system transforms unstructured regulatory data into a semantic knowledge graph, providing accurate, traceable, and context-aware responses.

---

## Modular Architecture
The repository is engineered for strict separation of concerns between data engineering and user inference:

### **`core_engine/GraphRag/`** — Knowledge Graph Backend
* **Ingestion**: Automated downloading and parsing of CMS NCD/LCD PDFs and CSVs using Spark-optimized parallel processing.
* **Storage**: Integrated with **Databricks Unity Catalog** at `/Volumes/research_catalog/healthcare/policy_docs/`.
* **Graph Construction**: LLM-driven entity and relationship extraction with incremental processing and auto-resume checkpoints.
* **Observability**: Fully instrumented with **MLflow Tracing** for latency and cost analysis.

### **`inference_interface/`** — Streamlit Frontend
* **User Interface**: Interactive natural language query portal with dynamic follow-up suggestions.
* **Visualization**: Real-time Knowledge Graph subgraph rendering using NetworkX and Matplotlib.
* **Performance**: Optimized with `@st.cache_data` for rapid loading of Parquet-based knowledge assets.

### **`app.py`** — Production Entry Point
The root `app.py` serves as a lightweight **Bridge (Shim)**. It ensures environmental path resolution between deployment platforms (Streamlit Cloud/Databricks Apps) and the modular codebase, maintaining a strict Single Source of Truth.

```python
# app.py acts as a production shim
import sys
import os

sys.path.append(os.path.join(os.getcwd(), "inference_interface"))

with open("inference_interface/app.py") as f:
    code = compile(f.read(), "inference_interface/app.py", 'exec')
    exec(code, globals())
```

---

## Data Infrastructure
The system leverages a hybrid storage and compute model:
* **Source Data**: `/Volumes/research_catalog/healthcare/policy_docs/input/`
* **Knowledge Assets**: `/Volumes/research_catalog/healthcare/policy_docs/output/` (Parquet format)
* **Compute**: Databricks Serverless for ingestion; Streamlit Cloud for global access.
* **Workspace ID**: `116488627034187`

---

## Deployment & Execution

### **Production Deployment (Streamlit Cloud)**
1. Connect this GitHub repository to the **Streamlit Cloud** dashboard.
2. Set the **Main file path** to: `app.py`.
3. Configure **Secrets** (Databricks Token, Host, and Model Name) in the Streamlit Cloud settings.

### **Local Development**
```bash
cd inference_interface
pip install -r requirements.txt
streamlit run app.py
```

### **Automated Data Sync**
The knowledge graph is refreshed via a scheduled Databricks Workflow pointing to:
**Notebook**: `core_engine/GraphRag/Create_Healthcare_Policy_Knowledge_GraphRAG`

Runs on **Databricks Serverless Compute** for automatic scaling and resource optimization.

---

## Technology Stack
* **Orchestration**: Python 3.10+, Spark SQL
* **AI Engine**: GraphRAG, Llama 3.3 70B (Mosaic AI Model Serving)
* **Observability**: MLflow Tracing
* **Frontend**: Streamlit
* **Storage**: Unity Catalog Volumes (Parquet)
* **Compute**: Databricks Serverless

---

## License

This project is licensed under the **MIT License**.

Copyright (c) 2026 Murali Menon

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Contact

For enterprise inquiries or technical support, contact muralimenon444@gmail.com.
