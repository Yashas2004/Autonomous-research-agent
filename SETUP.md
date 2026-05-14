# Setup & Installation Guide

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- OpenAI API key (get one at https://platform.openai.com/api-keys)

## Installation Steps

### 1. Clone the Repository

```bash
cd autonomous_research_agent
```

### 2. Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:

- **streamlit** - Web UI framework
- **openai** - OpenAI API client
- **chromadb** - Vector database
- **langchain_core** & **langchain_text_splitters** - Document processing
- **pymupdf** - PDF support
- **beautifulsoup4** - Web scraping
- **requests** - HTTP client
- **tiktoken** - Token counting

### 4. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Open .env with your text editor and set:
OPENAI_API_KEY=sk-your-actual-key-here
```

**Required variables:**

- `OPENAI_API_KEY` - Your OpenAI API key (required to run)

**Optional variables:**

- `OPENAI_MODEL` - Default: `gpt-4o` (use `gpt-4o-mini` to save costs)
- `AGENT_MAX_ITERATIONS` - Default: `10` (max ReAct loop cycles)
- `SIMILARITY_THRESHOLD` - Default: `0.6` (retrieval threshold)
- `CHUNK_SIZE` - Default: `1000` (document chunk size in chars)

### 5. Verify Installation

```bash
# Test if all imports work
python -c "import streamlit; from openai import OpenAI; import chromadb; print('✅ All imports successful')"
```

## Running the Application

### Start the Streamlit Server

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### First Run Checklist

1. ✅ See "🔬 Autonomous Research Agent" header
2. ✅ No "No OpenAI API key found" error
3. ✅ Control panel shows "● OpenAI Connected"
4. ✅ Sidebar shows "0 Chunks" initially
5. ✅ Can load sample documents

### Testing the Agent

Click **"📚 Load Sample Documents"** in the sidebar to ingest sample knowledge.

Then ask a question like:

- "Write an introduction to autonomous agents"
- "Summarize the key concepts from the documents"
- "Generate a 3-section report on AI and RAG"

## Troubleshooting

### Error: "No OpenAI API key found"

- Check that `.env` file exists in the same directory as `app.py`
- Verify `OPENAI_API_KEY=sk-...` is set correctly
- Your key must start with `sk-` and be at least 20 characters long
- Don't use quotes around the key in `.env`

### Error: "ModuleNotFoundError: No module named 'langchain_text_splitters'"

```bash
pip install langchain_text_splitters
```

### Error: "ModuleNotFoundError: No module named 'pymupdf'"

```bash
pip install pymupdf
```

### Slow Performance

- Reduce `AGENT_MAX_ITERATIONS` in `.env` to `5` or less
- Use `gpt-4o-mini` instead of `gpt-4o` to reduce latency
- Load fewer documents into the knowledge base

### Streamlit Not Opening Browser

Manually open `http://localhost:8501` in your browser

### Issues with PDF Upload

- Ensure PDFs are valid and not corrupted
- Try extracting text from PDF first to debug
- Fall back to TXT format if PDF extraction fails

## Project Structure

```
autonomous_research_agent/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── README.md                # Project documentation
├── SETUP.md                 # This file
├── data/
│   ├── chroma_db/           # Vector database (auto-created)
│   └── sample_docs/         # Sample documents for testing
│       ├── ai_intro.txt
│       ├── autonomous_agents.txt
│       └── rag_deep_dive.txt
└── src/
    ├── __init__.py
    ├── agent.py             # GPT-4o ReAct agent logic
    ├── ingestion.py         # Document loader & chunker
    ├── vectorstore.py       # ChromaDB + OpenAI embeddings
    ├── retrieval.py         # Vector search with filtering
    └── scraper.py           # Web scraper
```

## Performance Tips

1. **Faster responses**: Set `OPENAI_MODEL=gpt-4o-mini`
2. **Cheaper processing**: Use `gpt-4o-mini` (1/20th the cost)
3. **Reduce iterations**: Set `AGENT_MAX_ITERATIONS=5` for quicker agent loops
4. **Better quality**: Keep `gpt-4o` for complex research tasks

## Next Steps

1. ✅ Follow the installation steps above
2. ✅ Load sample documents to test functionality
3. ✅ Ingest your own documents via the UI
4. ✅ Scrape URLs to add web content
5. ✅ Generate reports and written sections

For more information, see [README.md](README.md)
