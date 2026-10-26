"""
AI Orchestra Conductor v2
Manages the orchestration of agents, tasks, and Crew execution
with support for thinking depth, search filters, and output language.
"""
import os
import sys

# Disable CrewAI telemetry to prevent network timeouts
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import time
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from crewai import Crew, Process, LLM
from agents import create_searcher_agent, create_solver_agent, create_writer_agent
from tasks import create_research_task, create_solve_task, create_write_task


class AIOrchestra:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._setup_environment()
        # Lazy Loading: LLMs are initialized only on-demand when agents perform
        self._search_llm: Optional[LLM] = None
        self._solver_llm: Optional[LLM] = None
        self._writer_llm: Optional[LLM] = None

    @property
    def search_llm(self) -> LLM:
        """Lazy load Searcher LLM only when Researcher agent is invoked."""
        if self._search_llm is None:
            self._search_llm = self._create_llm(
                model=self.config.get("SEARCH_MODEL", "gpt-4o-mini"),
                api_key=self.config.get("SEARCH_API_KEY", ""),
                base_url=self.config.get("SEARCH_BASE_URL") or self.config.get("OLLAMA_BASE_URL") or self.config.get("ROUTER_9_BASE_URL")
            )
        return self._search_llm

    @property
    def solver_llm(self) -> LLM:
        """Lazy load Solver LLM only when Problem Solver agent is invoked."""
        if self._solver_llm is None:
            self._solver_llm = self._create_llm(
                model=self.config.get("SOLVER_MODEL", "gpt-4o"),
                api_key=self.config.get("SOLVER_API_KEY", ""),
                base_url=self.config.get("SOLVER_BASE_URL") or self.config.get("OLLAMA_BASE_URL") or self.config.get("ROUTER_9_BASE_URL")
            )
        return self._solver_llm

    @property
    def writer_llm(self) -> LLM:
        """Lazy load Writer LLM only when Master Scribe agent is invoked."""
        if self._writer_llm is None:
            self._writer_llm = self._create_llm(
                model=self.config.get("WRITER_MODEL", "gpt-4o-mini"),
                api_key=self.config.get("WRITER_API_KEY", ""),
                base_url=self.config.get("WRITER_BASE_URL") or self.config.get("OLLAMA_BASE_URL") or self.config.get("ROUTER_9_BASE_URL")
            )
        return self._writer_llm

    def _setup_environment(self):
        """Set environment variables for third-party tools if present."""
        if self.config.get("SERPER_API_KEY"):
            os.environ["SERPER_API_KEY"] = self.config["SERPER_API_KEY"]
        if self.config.get("TAVILY_API_KEY"):
            os.environ["TAVILY_API_KEY"] = self.config["TAVILY_API_KEY"]

    def _create_llm(self, model: str, api_key: str, base_url: Optional[str] = None) -> LLM:
        """Create a CrewAI LLM instance with provider auto-resolution, 9Router, Ollama, and cloud mappings."""
        clean_model = model.strip()
        clean_key = api_key.strip() if api_key else ""

        # 1. 9Router local gateway integration (default port 20128)
        if clean_model.startswith("9router/") or (base_url and "20128" in base_url):
            resolved_url = base_url or os.environ.get("ROUTER_9_BASE_URL", "http://localhost:20128/v1")
            raw_model = clean_model
            if raw_model.startswith("9router/"):
                raw_model = raw_model.replace("9router/", "", 1)
            target_model = raw_model if raw_model.startswith("openai/") else f"openai/{raw_model}"
            return LLM(model=target_model, base_url=resolved_url, api_key=clean_key or "9router")

        # 2. Local Ollama integration (default port 11434)
        if clean_model.startswith("ollama/") or "ollama" in clean_model.lower() or (base_url and "11434" in base_url):
            resolved_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            if not clean_model.startswith("ollama/"):
                clean_model = f"ollama/{clean_model}"
            return LLM(model=clean_model, base_url=resolved_url, api_key="ollama")

        # Auto-upgrade deprecated Gemini model names
        deprecated_gemini = [
            "gemini-1.5-flash", "gemini/gemini-1.5-flash",
            "gemini-1.5-pro", "gemini/gemini-1.5-pro",
            "gemini-2.0-flash", "gemini/gemini-2.0-flash",
            "gemini-2.5-flash", "gemini/gemini-2.5-flash"
        ]
        if clean_model in deprecated_gemini or clean_model.endswith("gemini-1.5-flash") or clean_model.endswith("gemini-2.0-flash") or clean_model.endswith("gemini-2.5-flash"):
            clean_model = "gemini/gemini-3.8-flash"

        # Ensure correct environment variables are populated for providers
        if clean_key:
            if clean_key.startswith("AIzaSy") or "gemini" in clean_model.lower():
                os.environ["GEMINI_API_KEY"] = clean_key
            elif clean_key.startswith("gsk_") or "groq" in clean_model.lower():
                os.environ["GROQ_API_KEY"] = clean_key
            elif clean_key.startswith("sk-") and not clean_key.startswith("sk-ant-"):
                os.environ["OPENAI_API_KEY"] = clean_key

        return LLM(model=clean_model, api_key=clean_key if clean_key else None)

    def perform_symphony(self, query: str, settings: Optional[Dict[str, Any]] = None) -> Tuple[str, str, float]:
        """
        Executes the AI Orchestra symphony on the given user query.
        Args:
            query: The user's question or challenge.
            settings: Optional per-query settings dict with keys:
                      depth, depth_profile, domain_filter, language_filter, output_language.
        Returns: (final_report_text, output_filepath, elapsed_seconds)
        """
        settings = settings or {}

        # Store domain filter in env so the search tool can read it
        if settings.get("domain_filter"):
            os.environ["ORCHESTRA_DOMAIN_FILTER"] = settings["domain_filter"]
        else:
            os.environ.pop("ORCHESTRA_DOMAIN_FILTER", None)
        if settings.get("language_filter"):
            os.environ["ORCHESTRA_LANG_FILTER"] = settings["language_filter"]
        else:
            os.environ.pop("ORCHESTRA_LANG_FILTER", None)

        start_time = time.time()

        # 1. Assemble Musicians (Agents)
        out_lang = settings.get("output_language", "en")
        searcher = create_searcher_agent(llm=self.search_llm)
        solver = create_solver_agent(llm=self.solver_llm)
        writer = create_writer_agent(llm=self.writer_llm, language=out_lang)

        # 2. Assign Movements (Tasks) with settings
        task_research = create_research_task(searcher, query, settings)
        task_solve = create_solve_task(solver, query, task_research, settings)
        task_write = create_write_task(writer, query, task_research, task_solve, settings)

        # 3. Form Crew (The Orchestra)
        conductor = Crew(
            agents=[searcher, solver, writer],
            tasks=[task_research, task_solve, task_write],
            process=Process.sequential,
            verbose=True
        )

        # 4. Strike the baton!
        result = conductor.kickoff()
        elapsed = time.time() - start_time

        output_text = getattr(result, "raw", str(result))

        # 5. Save Output
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        depth_tag = settings.get("depth", "balanced")
        filename = f"orchestra_report_{depth_tag}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        metadata_header = (
            f"<!-- AI Orchestra Symphony Output -->\n"
            f"<!-- Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->\n"
            f"<!-- Duration: {elapsed:.2f} seconds -->\n"
            f"<!-- Thinking Depth: {depth_tag} -->\n"
            f"<!-- Query: {query} -->\n\n"
        )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(metadata_header + output_text)

        return output_text, filepath, elapsed
