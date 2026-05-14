"""
agent.py — Autonomous Research Agent (OpenAI GPT-4o + ReAct)

This is a TRUE research agent, not a QA bot.
It can:
  - Write introduction / background / conclusion sections
  - Synthesise information from multiple sources
  - Generate structured reports
  - Iteratively gather more info (from KB or web) before writing
  - Cite sources throughout
"""

from __future__ import annotations

import json
import logging
import os
import re
import textwrap
from typing import Callable, Optional

from openai import OpenAI

from src.retrieval import Retriever
from src.scraper import WebScraper
from src.ingestion import DocumentIngester

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

MODEL        = os.getenv("OPENAI_MODEL", "gpt-4o")
MAX_ITER     = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
MAX_TOKENS   = int(os.getenv("AGENT_MAX_TOKENS", "3000"))

# ── System Prompts ────────────────────────────────────────────────────────────

SYSTEM_RESEARCHER = """You are an Autonomous Research Agent with a PhD-level ability to synthesise information and produce well-structured written content.

You have access to TWO tools:
1. query_knowledge_base(query: str) → returns relevant text chunks + sources
2. scrape_web(url: str) → fetches and indexes a live URL

WORKFLOW — you MUST follow this loop:
  THOUGHT: Analyse the task. What information do I need? What kind of output is expected?
  ACTION: {"tool": "query_knowledge_base", "input": "specific search query"}
  OBSERVATION: [result]
  ... repeat gathering until you have enough material ...
  THOUGHT: I now have sufficient material. Let me plan the output structure.
  FINAL_ANSWER: [your complete, well-written response]

CRITICAL RULES:
- You are a WRITER and RESEARCHER, NOT a simple QA bot.
- If asked to write an "introduction", "section", "summary", "report", "overview", or any written content → produce rich, flowing prose — not bullet points.
- Always gather information via tools BEFORE writing. Never hallucinate.
- Query the KB multiple times with different angles to gather comprehensive material.
- Synthesise, connect ideas, and write in an authoritative academic/professional tone.
- Always cite sources inline like: [Source: filename.pdf] or [Source: url].
- Minimum response for written sections: 3-5 well-developed paragraphs.
- For reports: use clear headings, subheadings, and structured prose.

Output your reasoning in this EXACT format:
THOUGHT: ...
ACTION: {"tool": "...", "input": "..."}
OBSERVATION: [tool result]
THOUGHT: ...
FINAL_ANSWER: [full written response]"""

SYSTEM_QA = """You are a precise Research Assistant. Answer questions using only information from the knowledge base.

WORKFLOW:
  THOUGHT: What does the user need?
  ACTION: {"tool": "query_knowledge_base", "input": "search query"}
  OBSERVATION: [result]
  FINAL_ANSWER: [concise, factual answer with source citations]

Be concise but complete. Always cite sources. Do not hallucinate."""

SYSTEM_REPORT = """You are an expert Technical Writer and Research Analyst.

Your task: Produce a COMPLETE, STRUCTURED REPORT based on the knowledge base.

WORKFLOW:
1. THOUGHT: Plan the report structure (Title, Executive Summary, sections).
2. Gather information for EACH section via multiple tool calls.
3. Write the complete report.

FORMAT:
# [Report Title]
## Executive Summary
## 1. [Section]
## 2. [Section]
## 3. [Section]
## Conclusion
## References

Use clear professional prose. No bullet lists unless listing specific items. Cite all sources.

Output format:
THOUGHT: ...
ACTION: {"tool": "...", "input": "..."}
OBSERVATION: [tool result]
...
FINAL_ANSWER: [complete report]"""


def _pick_system(mode: str) -> str:
    if "Q&A" in mode or "concise" in mode.lower():
        return SYSTEM_QA
    if "Report" in mode or "report" in mode.lower():
        return SYSTEM_REPORT
    return SYSTEM_RESEARCHER


# ── Agent ─────────────────────────────────────────────────────────────────────

class ResearchAgent:
    def __init__(self, vectorstore):
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            
            self.client    = OpenAI(api_key=api_key)
            self.retriever = Retriever(vectorstore)
            self.scraper   = WebScraper()
            self.ingester  = DocumentIngester()
            self._context_chunks: list[str] = []
            logger.info("ResearchAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ResearchAgent: {e}")
            raise

    # ── Public entry point ────────────────────────────────────────────────────

    def run(
        self,
        question: str,
        mode: str = "Researcher (sections + synthesis)",
        web_enabled: bool = False,
        on_step: Optional[Callable[[dict], None]] = None,
        history: Optional[list] = None,
    ) -> dict:
        self._context_chunks = []
        self._on_step = on_step or (lambda x: None)
        self._web_enabled = web_enabled
        system = _pick_system(mode)

        # Build conversation
        messages = [{"role": "system", "content": system}]

        # Add recent history (last 6 turns)
        if history:
            for h in history[-6:]:
                role = "user" if h["role"] == "user" else "assistant"
                messages.append({"role": role, "content": h["content"]})

        messages.append({"role": "user", "content": question})

        return self._react_loop(messages)

    # ── ReAct loop ────────────────────────────────────────────────────────────

    def _react_loop(self, messages: list) -> dict:
        sources: list[str] = []

        for iteration in range(MAX_ITER):
            self._on_step({"type": "thought",
                           "content": f"Iteration {iteration + 1}/{MAX_ITER} — calling LLM…"})

            try:
                response = self.client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    temperature=0.4,
                )
            except Exception as e:
                logger.error(f"LLM call failed at iteration {iteration + 1}: {e}")
                return {
                    "answer": f"Error during processing: {str(e)}",
                    "sources": list(dict.fromkeys(sources))
                }
            
            text = response.choices[0].message.content
            if not text:
                logger.warning("LLM returned empty content")
                return {
                    "answer": "Error: LLM returned empty response",
                    "sources": list(dict.fromkeys(sources))
                }
            text = text.strip()

            # Check for FINAL_ANSWER
            if "FINAL_ANSWER:" in text:
                answer = text.split("FINAL_ANSWER:", 1)[1].strip()
                self._on_step({"type": "final", "content": "Writing final response…"})
                return {"answer": answer, "sources": list(dict.fromkeys(sources))}

            # Parse THOUGHT
            if "THOUGHT:" in text:
                thought = self._extract_block(text, "THOUGHT")
                if thought:
                    self._on_step({"type": "thought", "content": thought[:200]})

            # Parse ACTION
            if "ACTION:" in text:
                action_raw = self._extract_block(text, "ACTION")
                tool_name, tool_input = self._parse_action(action_raw)

                self._on_step({"type": "action",
                               "content": f"{tool_name}({tool_input[:80]})"})

                # Execute tool
                observation, new_sources = self._execute_tool(tool_name, tool_input)
                sources.extend(new_sources)

                self._on_step({"type": "observation",
                               "content": f"Got {len(observation)} chars from {tool_name}"})

                # Append to conversation
                messages.append({"role": "assistant", "content": text})
                messages.append({
                    "role": "user",
                    "content": f"OBSERVATION: {observation}\n\nContinue your research or write FINAL_ANSWER if you have enough."
                })
            else:
                # Model responded without an action — treat as final
                return {"answer": text, "sources": list(dict.fromkeys(sources))}

        # Exhausted iterations — ask for summary
        messages.append({
            "role": "user",
            "content": "You have reached the maximum iterations. Write your FINAL_ANSWER now using all gathered information."
        })
        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=0.4,
            )
            final_text = response.choices[0].message.content
            if not final_text:
                final_text = "Unable to generate final response"
            else:
                final_text = final_text.strip()
                if "FINAL_ANSWER:" in final_text:
                    final_text = final_text.split("FINAL_ANSWER:", 1)[1].strip()
        except Exception as e:
            logger.error(f"Failed to generate final response: {e}")
            final_text = f"Error generating response: {str(e)}"
        
        return {"answer": final_text, "sources": list(dict.fromkeys(sources))}

    # ── Tool executor ─────────────────────────────────────────────────────────

    def _execute_tool(self, tool: str, tool_input: str) -> tuple[str, list[str]]:
        sources: list[str] = []

        if tool == "query_knowledge_base":
            results = self.retriever.retrieve(tool_input, k=6)
            if not results:
                return "No relevant information found in the knowledge base for this query.", []

            parts = []
            for r in results:
                src = r.metadata.get("source", r.metadata.get("file_name", "unknown"))
                chunk_text = r.page_content.strip()
                parts.append(f"[Source: {src}]\n{chunk_text}")
                if src not in sources:
                    sources.append(src)

            return "\n\n---\n\n".join(parts), sources

        elif tool == "scrape_web":
            if not self._web_enabled:
                return "Web scraping is disabled. Enable it in the sidebar.", []

            url = tool_input.strip().strip('"\'')
            try:
                docs = self.scraper.scrape(url)
                if not docs:
                    return f"Could not extract content from {url}.", []

                chunks = self.ingester.process_and_chunk(docs)
                # Optionally add to vectorstore (already done via Retriever's VS ref)

                combined = "\n\n".join(d.page_content[:600] for d in docs[:3])
                title = docs[0].metadata.get("title", url)
                sources.append(f"{title} ({url})")
                return f"Scraped content from {url}:\n\n{combined}", sources
            except Exception as e:
                return f"Error scraping {url}: {e}", []

        else:
            return f"Unknown tool: {tool}. Use 'query_knowledge_base' or 'scrape_web'.", []

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_block(text: str, label: str) -> str:
        """Extract content after a label up to the next label."""
        pattern = rf"{label}:\s*(.*?)(?=\n(?:THOUGHT|ACTION|OBSERVATION|FINAL_ANSWER):|$)"
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _parse_action(action_str: str) -> tuple[str, str]:
        """Parse JSON action or fallback."""
        action_str = action_str.strip()
        # Try JSON
        try:
            # Extract JSON even if wrapped in text
            json_match = re.search(r'\{.*\}', action_str, re.DOTALL)
            if json_match:
                obj = json.loads(json_match.group())
                tool  = obj.get("tool", "query_knowledge_base")
                inp   = obj.get("input", obj.get("query", obj.get("url", "")))
                return tool, str(inp)
        except json.JSONDecodeError:
            pass

        # Fallback: detect scrape vs query
        if "scrape_web" in action_str or "http" in action_str:
            url_match = re.search(r'https?://\S+', action_str)
            return "scrape_web", url_match.group() if url_match else action_str

        # Default to KB query
        return "query_knowledge_base", action_str
