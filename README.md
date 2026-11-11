# Adaptive RAG

An intelligent Retrieval-Augmented Generation system that dynamically routes queries to indexed documents, general knowledge, or live web search using a LangGraph-powered agentic pipeline.

**[Live Demo](http://localhost:8501)** | **[API Docs](http://localhost:8000/docs)**

---

## What It Does

Upload documents (PDF/TXT), then ask questions. The system automatically decides the best way to answer:

- **Index** — retrieves from your uploaded documents via vector search
- **General** — answers from the LLM's built-in knowledge
- **Search** — fetches real-time results from the web via Tavily

The pipeline includes query rewriting, relevance grading, and answer verification to ensure accurate responses.

---

## Architecture

```
User Query
    ↓
Query Classifier (LLM)
    ↓
┌────────────┬──────────────┬──────────────┐
│  Index     │   General    │   Web Search │
│  (FAISS)   │   (LLM)     │   (Tavily)   │
└─────┬──────┴──────┬───────┴──────┬───────┘
      ↓             ↓              ↓
  Relevance     Direct        Relevance
   Grading       Answer       Grading
      ↓                          ↓
  Rewrite Query              Generate Answer
  (if not relevant)              ↓
      ↓                      Final Response
  Retrieve Again
```

**Key Components:**
- **LangGraph** — orchestrates the multi-step agentic workflow
- **ReAct Agent** — handles document retrieval with reasoning
- **FAISS / Qdrant** — vector storage for document embeddings
- **MongoDB** — persistent chat history and session management
- **FastAPI** — REST API backend
- **Streamlit** — interactive web UI

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq (LLaMA 3) |
| Framework | LangChain, LangGraph |
| Embeddings | HuggingFace (all-MiniLM-L6-v2) |
| Vector DB | FAISS (local), Qdrant (production) |
| Backend | FastAPI, Uvicorn |
| Frontend | Streamlit |
| Database | MongoDB (Motor async driver) |
| Web Search | Tavily API |
| Validation | Pydantic |

---

## Project Structure

```
Adaptive-Rag/
├── src/
│   ├── main.py                  # FastAPI entry point
│   ├── api/routes.py            # API endpoints
│   ├── config/prompts.yaml      # LLM prompt templates
│   ├── core/config.py           # Environment settings
│   ├── db/mongo_client.py       # MongoDB client
│   ├── llms/groq.py             # LLM initialization
│   ├── memory/                  # Chat history (MongoDB + in-memory)
│   ├── models/                  # Pydantic schemas
│   ├── rag/
│   │   ├── graph_builder.py     # LangGraph workflow
│   │   ├── nodes.py             # Graph node implementations
│   │   ├── retriever_setup.py   # Vector store setup
│   │   ├── document_upload.py   # Document processing
│   │   └── reAct_agent.py       # ReAct agent
│   └── tools/
│       ├── common_tools.py      # Utility functions
│       └── graph_tools.py       # Routing logic
├── streamlit_app/
│   ├── home.py                  # Main UI page
│   ├── pages/chat.py            # Chat interface
│   └── utils/api_client.py      # Backend API client
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB (local or cloud)
- API keys: Groq, Tavily (optional)

### Installation

```bash
git clone https://github.com/DivayJainDJ/Adaptive-Rag.git
cd Adaptive-Rag
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
MONGODB_URL=mongodb://localhost:27017
```

### Run

**Backend** (Terminal 1):
```bash
python -m uvicorn src.main:app --reload --port 8000
```

**Frontend** (Terminal 2):
```bash
streamlit run streamlit_app/home.py
```

Open http://localhost:8501 to use the app.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/rag/query` | Send a question and get a RAG response |
| `POST` | `/rag/documents/upload` | Upload a document for indexing |
| `GET` | `/` | Health check |

**Query example:**
```json
POST /rag/query
{
  "query": "What are the key findings in the report?",
  "session_id": "user_123"
}
```

**Upload example:**
```bash
curl -X POST http://localhost:8000/rag/documents/upload \
  -H "X-Description: Research paper on AI safety" \
  -F "file=@paper.pdf"
```

---

## How It Works

1. **Upload** — Documents are chunked (1000 chars, 150 overlap), embedded with HuggingFace, and stored in FAISS
2. **Classify** — The LLM classifies each query as index/general/search
3. **Retrieve** — For index queries, a ReAct agent searches the vector store
4. **Grade** — Retrieved documents are scored for relevance
5. **Rewrite** — If relevance is low, the query is rewritten and re-retrieved
6. **Generate** — The final answer is synthesized from the best context

---

## Evaluation: does routing help?

20 questions (10 answerable only from an indexed handbook, 6 general
knowledge, 4 needing live search) are run twice: once through the real graph
with LLM query classification, and once through the same graph with
classification removed (`compile_graph(force_route="index")`, so every question
is answered from the vector index). A keyword check decides whether each
answer actually contains the expected fact.

```bash
python run_eval.py          # writes eval/routing_results.json
```

| Arm | Relevant answers |
|---|---|
| With adaptive routing | **20 / 20 (100%)** |
| Without routing (index only) | 10 / 20 (50%) |

Without routing, every non-handbook question gets "I do not have that
information" — the index route never reaches the model's own knowledge or the
web. The last run used `qwen/qwen3.8-27b` because the account's daily token
budget for `openai/gpt-oss-20b` was exhausted; both arms used the same model,
so the comparison holds. See [`eval/README.md`](eval/README.md) for the
protocol, the questions, and the per-question answers in
[`eval/routing_results.json`](eval/routing_results.json).

Limitations: relevance is a substring check, not an LLM judge, and the run made
live Tavily searches, so search-question answers vary between runs.

---

## Author

**Divay Jain**
- GitHub: [DivayJainDJ](https://github.com/DivayJainDJ)

---

## License

MIT
