import streamlit as st
import os
import sys
import tempfile
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Autonomous Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a26;
    --border: #2a2a3d;
    --accent: #6c63ff;
    --accent2: #00d4aa;
    --accent3: #ff6b6b;
    --text: #e8e8f0;
    --muted: #7070a0;
}

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp { background: var(--bg); }

/* Header */
.agent-header {
    background: linear-gradient(135deg, #0d0d1a 0%, #12122a 50%, #0a1520 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.agent-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -20%;
    width: 60%;
    height: 200%;
    background: radial-gradient(ellipse, rgba(108,99,255,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.agent-header::after {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 50%;
    height: 200%;
    background: radial-gradient(ellipse, rgba(0,212,170,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.agent-title {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #6c63ff 0%, #00d4aa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}
.agent-subtitle {
    color: var(--muted);
    font-size: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 0.4rem;
    letter-spacing: 0.05em;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--accent2) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, #4f46e5 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(108,99,255,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(108,99,255,0.45) !important;
}

/* Chat messages */
.user-msg {
    background: linear-gradient(135deg, var(--surface2) 0%, #1e1e30 100%);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    font-size: 0.95rem;
}
.agent-msg {
    background: linear-gradient(135deg, #0d1a15 0%, #0a1a12 100%);
    border: 1px solid #1a3a2a;
    border-left: 3px solid var(--accent2);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    font-size: 0.95rem;
    line-height: 1.7;
}

/* Thought steps */
.thought-step {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin: 0.3rem 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
}
.thought-step.thinking { border-left: 3px solid #f59e0b; color: #f59e0b; }
.thought-step.action   { border-left: 3px solid var(--accent); color: var(--accent); }
.thought-step.observe  { border-left: 3px solid var(--accent2); color: var(--accent2); }
.thought-step.final    { border-left: 3px solid #22c55e; color: #22c55e; }

/* Status badges */
.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
    letter-spacing: 0.05em;
}
.badge-online  { background: rgba(34,197,94,0.15); color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }
.badge-offline { background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
.badge-web     { background: rgba(108,99,255,0.15); color: var(--accent); border: 1px solid rgba(108,99,255,0.3); }

/* Sources */
.source-chip {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--muted);
    margin: 0.2rem;
}

/* Input */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Syne', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(108,99,255,0.2) !important;
}

/* Toggle */
.stToggle > div { color: var(--text) !important; }

/* File uploader */
.stFileUploader > div {
    background: var(--surface) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 10px !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--muted) !important;
    font-size: 0.8rem !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}

/* Metrics */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.metric-label {
    font-size: 0.7rem;
    color: var(--muted);
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.25rem;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* Info box */
.stInfo { background: rgba(108,99,255,0.1) !important; border: 1px solid rgba(108,99,255,0.3) !important; }
.stSuccess { background: rgba(34,197,94,0.1) !important; border: 1px solid rgba(34,197,94,0.3) !important; }
.stWarning { background: rgba(245,158,11,0.1) !important; border: 1px solid rgba(245,158,11,0.3) !important; }
.stError { background: rgba(239,68,68,0.1) !important; border: 1px solid rgba(239,68,68,0.3) !important; }

div[data-testid="stMarkdownContainer"] p { line-height: 1.7; }
</style>
""", unsafe_allow_html=True)


def check_api_key():
    """Validate OpenAI API key exists and is properly formatted."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return bool(key and key.startswith("sk-")) and len(key) > 20


def init_components():
    """Initialize session state components with error handling."""
    try:
        if "vectorstore" not in st.session_state:
            from src.vectorstore import VectorStoreManager
            st.session_state.vectorstore = VectorStoreManager()
            logger.info("Vectorstore initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize vectorstore: {e}")
        st.error(f"⚠️  Failed to initialize vector database: {str(e)}")
        st.stop()

    try:
        if "agent" not in st.session_state:
            from src.agent import ResearchAgent
            st.session_state.agent = ResearchAgent(st.session_state.vectorstore)
            logger.info("Research agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        st.error(f"⚠️  Failed to initialize research agent: {str(e)}")
        st.stop()

    # Initialize session state variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "web_enabled" not in st.session_state:
        st.session_state.web_enabled = False
    if "agent_mode" not in st.session_state:
        st.session_state.agent_mode = "Researcher (sections + synthesis)"


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="agent-header">
    <div class="agent-title">🔬 Auto-Search</div>
    <div class="agent-subtitle">Wanna research something?</div>
</div>
""", unsafe_allow_html=True)

# ── API key gate ─────────────────────────────────────────────────────────────
if not check_api_key():
    st.error("⚠️  No OpenAI API key found. Add `OPENAI_API_KEY=sk-...` to your `.env` file and restart.")
    st.code("OPENAI_API_KEY=sk-your-key-here", language="bash")
    st.stop()

init_components()
vs   = st.session_state.vectorstore
agent = st.session_state.agent

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")

    # Status
    api_ok = check_api_key()
    st.markdown(f"""
    <div style='margin-bottom:1rem;'>
        <span class='status-badge badge-{"online" if api_ok else "offline"}'>
            {"● OpenAI Connected" if api_ok else "● No API Key"}
        </span>
        &nbsp;
        <span class='status-badge badge-{"web" if st.session_state.web_enabled else "offline"}'>
            {"🌐 Web ON" if st.session_state.web_enabled else "📵 Web OFF"}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    try:
        count = vs.collection.count()
    except Exception:
        count = 0
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{count}</div>
            <div class='metric-label'>Chunks</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{len(st.session_state.messages)}</div>
            <div class='metric-label'>Messages</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Web toggle
    st.markdown("### 🌐 Web Search")
    st.session_state.web_enabled = st.toggle(
        "Enable web scraping fallback",
        value=st.session_state.web_enabled,
        help="Agent will scrape the web if local KB is insufficient"
    )

    st.markdown("---")
    st.markdown("### 📂 Knowledge Base")

    # Sample docs
    sample_path = Path(__file__).parent / "data" / "sample_docs"
    if st.button("📚 Load Sample Documents", use_container_width=True):
        try:
            if sample_path.exists():
                from src.ingestion import DocumentIngester
                ingester = DocumentIngester()
                with st.spinner("Ingesting sample documents…"):
                    docs = ingester.ingest_data_folder(str(sample_path))
                    added = vs.add_documents(docs)
                st.success(f"✅ Loaded {added} new chunks")
            else:
                st.warning("No sample_docs folder found.")
        except Exception as e:
            logger.error(f"Error loading sample docs: {e}")
            st.error(f"Error loading documents: {str(e)}") 

    # File upload
    uploaded = st.file_uploader(
        "Upload TXT / PDF",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded and st.button("⬆️ Ingest Uploaded Files", use_container_width=True):
        try:
            from src.ingestion import DocumentIngester
            ingester = DocumentIngester()
            total = 0
            with st.spinner("Processing files…"):
                for f in uploaded:
                    # Use tempfile instead of /tmp/ for cross-platform compatibility
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f.name).suffix) as tmp_file:
                        tmp_file.write(f.read())
                        tmp_path = tmp_file.name
                    try:
                        docs = ingester.load_single_file(tmp_path)
                        chunks = ingester.process_and_chunk(docs)
                        vs.add_documents(chunks)
                        total += len(chunks)
                    finally:
                        # Clean up temp file
                        try:
                            Path(tmp_path).unlink()
                        except Exception as e:
                            logger.debug(f"Could not delete temp file {tmp_path}: {e}")
            st.success(f"✅ Added {total} chunks")
        except Exception as e:
            logger.error(f"Error ingesting files: {e}")
            st.error(f"Error processing files: {str(e)}")

    # URL scrape
    st.markdown("### 🕸️ Scrape URL")
    url_input = st.text_input("Paste URL", placeholder="https://example.com/article", label_visibility="collapsed")
    if st.button("🔍 Scrape & Ingest", use_container_width=True) and url_input:
        try:
            from src.scraper import WebScraper
            from src.ingestion import DocumentIngester
            scraper = WebScraper()
            ingester = DocumentIngester()
            with st.spinner(f"Scraping {url_input}…"):
                docs = scraper.scrape(url_input)
                if docs:
                    chunks = ingester.process_and_chunk(docs)
                    added = vs.add_documents(chunks)
                    st.success(f"✅ Scraped {added} new chunks")
                else:
                    st.error("Could not scrape content from that URL.")
        except Exception as e:
            logger.error(f"Error scraping URL: {e}")
            st.error(f"Error scraping URL: {str(e)}")

    st.markdown("---")

    # Agent mode selector
    st.markdown("### 🧠 Agent Mode")
    mode = st.selectbox(
        "Response style",
        ["Researcher (sections + synthesis)",
         "Q&A (concise answers)",
         "Report (structured document)"],
        label_visibility="collapsed"
    )
    st.session_state.agent_mode = mode

    st.markdown("---")
    if st.button("🗑️ Clear Knowledge Base", use_container_width=True):
        vs.delete_collection()
        st.success("Knowledge base cleared.")

    if st.button("💬 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Main Chat Area ────────────────────────────────────────────────────────────
col_chat, col_info = st.columns([3, 1])

with col_chat:
    # Chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""<div class='user-msg'>👤 &nbsp;<strong>You</strong><br><br>{msg['content']}</div>""",
                        unsafe_allow_html=True)
        else:
            content = msg["content"]
            sources_html = ""
            if msg.get("sources"):
                chips = "".join(f"<span class='source-chip'>📄 {s}</span>" for s in msg["sources"][:6])
                sources_html = f"<div style='margin-top:0.75rem;border-top:1px solid #2a2a3d;padding-top:0.5rem;'>{chips}</div>"
            st.markdown(
                f"""<div class='agent-msg'>🔬 &nbsp;<strong>Research Agent</strong><br><br>{content}{sources_html}</div>""",
                unsafe_allow_html=True)

    # Input
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Ask the research agent…",
            placeholder="e.g. Write an introduction section about autonomous agents\n     Summarize the key concepts from the ingested documents\n     Compare RAG vs fine-tuning approaches",
            height=90,
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("🚀 Send", use_container_width=True)

    if submitted and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})

        mode = st.session_state.get("agent_mode", "Researcher (sections + synthesis)")
        web  = st.session_state.web_enabled

        with st.spinner("Agent is thinking…"):
            thought_placeholder = st.empty()
            thoughts_log = []

            def on_step(step: dict):
                thoughts_log.append(step)
                html = ""
                for s in thoughts_log[-6:]:
                    cls  = {"thought": "thinking", "action": "action",
                            "observation": "observe", "final": "final"}.get(s["type"], "thinking")
                    icon = {"thought": "💭", "action": "⚡", "observation": "👁️", "final": "✅"}.get(s["type"], "💭")
                    html += f"<div class='thought-step {cls}'>{icon} {s['content'][:120]}</div>"
                thought_placeholder.markdown(html, unsafe_allow_html=True)

            try:
                result = agent.run(
                    question=user_input.strip(),
                    mode=mode,
                    web_enabled=web,
                    on_step=on_step,
                    history=st.session_state.messages[:-1]
                )
            except Exception as e:
                logger.error(f"Agent error: {e}")
                thought_placeholder.empty()
                st.error(f"⚠️  Agent error: {str(e)}")
                st.session_state.messages.pop()  # Remove the user message if agent fails
                st.stop()

        thought_placeholder.empty()

        st.session_state.messages.append({
            "role": "assistant",
            "content": result.get("answer", "No response generated"),
            "sources": result.get("sources", [])
        })
        st.rerun()

with col_info:
    st.markdown("""
    <div style='background:#12121a;border:1px solid #2a2a3d;border-radius:12px;padding:1.25rem;'>
        <div style='font-size:0.7rem;color:#7070a0;font-family:JetBrains Mono,monospace;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1rem;'>
            What I can do
        </div>
        <div style='font-size:0.82rem;color:#a0a0c0;line-height:2;'>
            ✍️ Write <strong style="color:#e8e8f0">sections & introductions</strong><br>
            📋 Create <strong style="color:#e8e8f0">structured reports</strong><br>
            🔍 Deep-dive <strong style="color:#e8e8f0">research synthesis</strong><br>
            🌐 Scrape & learn from <strong style="color:#e8e8f0">live web</strong><br>
            📄 Cite <strong style="color:#e8e8f0">sources</strong> from KB<br>
            🧩 Compare & <strong style="color:#e8e8f0">contrast ideas</strong><br>
        </div>
    </div>
    <br>
    <div style='background:#12121a;border:1px solid #2a2a3d;border-radius:12px;padding:1.25rem;'>
        <div style='font-size:0.7rem;color:#7070a0;font-family:JetBrains Mono,monospace;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1rem;'>
            Example prompts
        </div>
        <div style='font-size:0.78rem;color:#7070a0;line-height:2.2;'>
            <em>"Write an introduction to autonomous agents"</em><br>
            <em>"Summarize what the docs say about RAG"</em><br>
            <em>"Generate a 3-section report on LLMs"</em><br>
            <em>"What are the key differences between…"</em>
        </div>
    </div>
    """, unsafe_allow_html=True)
