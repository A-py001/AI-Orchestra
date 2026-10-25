"""
Interactive Configuration Manager for AI Orchestra v2.1
Handles environment setup, API keys, model tier selection,
advanced customization, and Local Ollama auto-detection.
"""
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
from typing import List, Tuple
from dotenv import load_dotenv, set_key
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from tools.ollama_detector import detect_ollama, ensure_ollama_service
from tools.language_detector import detect_language, normalize_language

console = Console()
ENV_FILE = ".env"

# ─── Model Tier Catalogs ─────────────────────────────────────────────
MODEL_TIERS = {
    "gemini": {
        "light":    "gemini/gemini-3.8-flash-lite",
        "balanced": "gemini/gemini-3.8-flash",
        "heavy":    "gemini/gemini-3.5-flash",
    },
    "openai": {
        "light":    "gpt-4o-mini",
        "balanced": "gpt-4o",
        "heavy":    "o3-mini",
    },
    "groq": {
        "light":    "groq/llama-3.1-8b-instant",
        "balanced": "groq/llama-3.3-70b-versatile",
        "heavy":    "groq/llama-3.3-70b-versatile",
    },
}

def _detect_provider(model_or_key: str) -> str:
    s = (model_or_key or "").strip()
    if s.startswith("ollama/") or "ollama" in s.lower():
        return "ollama"
    if s.startswith("AIzaSy"):
        return "gemini"
    if s.startswith("gsk_"):
        return "groq"
    return "openai"

def load_existing_env():
    if os.path.exists(ENV_FILE):
        load_dotenv(ENV_FILE, override=True)

def show_current_config(config: dict):
    table = Table(title="🎛️ Current AI Orchestra Configuration", border_style="cyan")
    table.add_column("Orchestra Role", style="bold yellow")
    table.add_column("AI Model", style="green")
    table.add_column("API Key / Endpoint", style="magenta")

    def format_status(role_key: str, key_val: str, base_url_val: str = ""):
        m = config.get(role_key, "")
        if "ollama" in m.lower():
            url_hint = base_url_val or "http://localhost:11434"
            return f"[bold green]Local ({url_hint})[/bold green]"
        if not key_val:
            return "[red]Not Set[/red]"
        if len(key_val) <= 8:
            return "[green]Configured[/green]"
        return f"[green]{key_val[:4]}...{key_val[-4:]}[/green]"

    table.add_row(
        "🎻 1. Searcher Agent (Researcher)",
        config.get("SEARCH_MODEL", "-"),
        format_status("SEARCH_MODEL", config.get("SEARCH_API_KEY", ""), config.get("SEARCH_BASE_URL", ""))
    )
    table.add_row(
        "🎹 2. Problem Solver Agent (Soloist)",
        config.get("SOLVER_MODEL", "-"),
        format_status("SOLVER_MODEL", config.get("SOLVER_API_KEY", ""), config.get("SOLVER_BASE_URL", ""))
    )
    table.add_row(
        "🎺 3. Writer Agent (Master Scribe)",
        config.get("WRITER_MODEL", "-"),
        format_status("WRITER_MODEL", config.get("WRITER_API_KEY", ""), config.get("WRITER_BASE_URL", ""))
    )

    # Ollama Auto-Detection Badge
    is_active, detected_models = detect_ollama()
    if is_active:
        m_str = ", ".join(detected_models[:3]) if detected_models else "None loaded"
        if len(detected_models) > 3:
            m_str += f" (+{len(detected_models) - 3} more)"
        table.add_row("🦙 Local Ollama Service", f"[bold green]Online ({m_str})[/bold green]", "[green]Auto-Detected[/green]")
    elif detected_models:
        m_str = ", ".join(detected_models[:3])
        table.add_row("🦙 Local Ollama Service", f"[bold yellow]Offline on port 11434 ({m_str})[/bold yellow]", "[yellow]Auto-Detected[/yellow]")
    else:
        table.add_row("🦙 Local Ollama Service", "[dim]Not Detected[/dim]", "[dim]N/A[/dim]")

    search_tool_info = "DuckDuckGo / Free Web Search (Active)"
    if config.get("SERPER_API_KEY"):
        search_tool_info = f"Google Serper ({config['SERPER_API_KEY'][:4]}...)"
    elif config.get("TAVILY_API_KEY"):
        search_tool_info = f"Tavily Search ({config['TAVILY_API_KEY'][:4]}...)"
    table.add_row("🌐 Web Search Engine", search_tool_info, "[blue]Auto Fallback[/blue]")

    console.print(table)

def _pick_model_tier(provider: str, role_label: str) -> str:
    """Let the user pick a model tier (light / balanced / heavy / custom) for cloud providers."""
    tiers = MODEL_TIERS.get(provider, MODEL_TIERS["openai"])
    console.print(f"\n[bold]  Select model power for {role_label}:[/bold]")
    console.print(f"    [green]1[/green]) ⚡ Light / Fast   → [dim]{tiers['light']}[/dim]")
    console.print(f"    [green]2[/green]) ⚖️  Balanced      → [dim]{tiers['balanced']}[/dim]")
    console.print(f"    [green]3[/green]) 🧠 Heavy / Pro    → [dim]{tiers['heavy']}[/dim]")
    console.print(f"    [green]4[/green]) ✍️  Custom (type any model name)")
    tier_choice = Prompt.ask("  Tier", choices=["1", "2", "3", "4"], default="2")
    if tier_choice == "1":
        return tiers["light"]
    elif tier_choice == "3":
        return tiers["heavy"]
    elif tier_choice == "4":
        return Prompt.ask("  Enter custom model name")
    return tiers["balanced"]

def _pick_ollama_model(role_label: str, detected_models: List[str]) -> Tuple[str, str]:
    """
    Select or input an Ollama model.
    Returns: (model_name_with_ollama_prefix, base_url)
    """
    console.print(f"\n[bold cyan]  Select Local Ollama Model for {role_label}:[/bold cyan]")
    choices = []
    if detected_models:
        console.print("[dim]  Detected local models on your machine:[/dim]")
        for i, m in enumerate(detected_models, 1):
            choices.append(str(i))
            rec_tag = " (Recommended)" if i == 1 else ""
            console.print(f"    [green]{i}[/green]) [bold]{m}[/bold]{rec_tag}")
        choices.append(str(len(detected_models) + 1))
        console.print(f"    [green]{len(detected_models) + 1}[/green]) ✍️  Type other model name")
        
        pick = Prompt.ask("  Model choice", choices=choices, default="1")
        idx = int(pick) - 1
        if idx < len(detected_models):
            chosen = detected_models[idx]
        else:
            chosen = Prompt.ask("  Enter Ollama model name (e.g. llama3.2, mistral, qwen2.5)")
    else:
        console.print("[yellow]  No models detected automatically. You can enter your model name:[/yellow]")
        chosen = Prompt.ask("  Enter Ollama model name (e.g. qwen2.5-coder:7b)", default="qwen2.5-coder:7b")

    clean_model = f"ollama/{chosen}" if not chosen.startswith("ollama/") else chosen
    base_url = "http://localhost:11434"
    return clean_model, base_url

def _ask_api_key(prompt_text: str, default_key: str = "") -> str:
    """Prompt for API key cleanly without getpass clipboard eating, showing masked hint."""
    hint = f" [current: {default_key[:4]}...{default_key[-4:]}]" if len(default_key) > 8 else ""
    console.print(f"\n[cyan]{prompt_text}{hint}[/cyan]")
    console.print("[dim](Paste your API key and press Enter. Press Enter directly to keep current key)[/dim]")
    val = Prompt.ask("Key").strip()
    if not val and default_key:
        return default_key
    if val:
        mask = f"{val[:4]}...{val[-4:]}" if len(val) > 8 else "Set"
        console.print(f"[green]✔ Key registered: {mask}[/green]")
    return val

def save_config_to_env(config: dict):
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write("# AI Orchestra Environment Variables\n")
    for k, v in config.items():
        if v:
            set_key(ENV_FILE, k, str(v))
            os.environ[k] = str(v)

    # Synchronize standard provider environment variables
    main_key = config.get("SEARCH_API_KEY", "") or config.get("SOLVER_API_KEY", "")
    if main_key:
        if main_key.startswith("AIzaSy"):
            set_key(ENV_FILE, "GEMINI_API_KEY", main_key)
            os.environ["GEMINI_API_KEY"] = main_key
        elif main_key.startswith("sk-") and not main_key.startswith("sk-ant-"):
            set_key(ENV_FILE, "OPENAI_API_KEY", main_key)
            os.environ["OPENAI_API_KEY"] = main_key
        elif main_key.startswith("gsk_"):
            set_key(ENV_FILE, "GROQ_API_KEY", main_key)
            os.environ["GROQ_API_KEY"] = main_key

def get_orchestra_config(force_reconfigure: bool = False) -> dict:
    load_existing_env()

    existing_search_key = os.environ.get("SEARCH_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    existing_solver_key = os.environ.get("SOLVER_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    existing_writer_key = os.environ.get("WRITER_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""

    config = {
        "SEARCH_MODEL": os.environ.get("SEARCH_MODEL", "gemini/gemini-3.8-flash"),
        "SEARCH_API_KEY": existing_search_key,
        "SEARCH_BASE_URL": os.environ.get("SEARCH_BASE_URL", ""),
        "SOLVER_MODEL": os.environ.get("SOLVER_MODEL", "gemini/gemini-3.8-flash"),
        "SOLVER_API_KEY": existing_solver_key,
        "SOLVER_BASE_URL": os.environ.get("SOLVER_BASE_URL", ""),
        "WRITER_MODEL": os.environ.get("WRITER_MODEL", "gemini/gemini-3.8-flash"),
        "WRITER_API_KEY": existing_writer_key,
        "WRITER_BASE_URL": os.environ.get("WRITER_BASE_URL", ""),
        "OLLAMA_BASE_URL": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        "SERPER_API_KEY": os.environ.get("SERPER_API_KEY", ""),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", ""),
    }

    # Normalize model strings from env if needed
    for model_key in ["SEARCH_MODEL", "SOLVER_MODEL", "WRITER_MODEL"]:
        m = config[model_key]
        if "gemini" in m.lower() and not m.startswith("gemini/"):
            clean_m = m.lower().replace(" ", "-")
            config[model_key] = f"gemini/{clean_m}"

    # Determine if already configured (either with cloud keys or local ollama models)
    has_any_keys = bool(
        ("ollama" in config["SEARCH_MODEL"].lower() or config["SEARCH_API_KEY"]) and
        ("ollama" in config["SOLVER_MODEL"].lower() or config["SOLVER_API_KEY"]) and
        ("ollama" in config["WRITER_MODEL"].lower() or config["WRITER_API_KEY"])
    )

    if has_any_keys and not force_reconfigure:
        show_current_config(config)
        use_saved = Confirm.ask("Do you want to continue with the current saved configuration?", default=True)
        if use_saved:
            # If using Ollama, ensure service is online
            if any("ollama" in config[k].lower() for k in ["SEARCH_MODEL", "SOLVER_MODEL", "WRITER_MODEL"]):
                ensure_ollama_service()
            return config

    # Scan Ollama
    is_active, detected_models = detect_ollama()
    ollama_badge = ""
    if is_active:
        ollama_badge = f"\n[green]🟢 Local Ollama Online: Found {len(detected_models)} models ({', '.join(detected_models[:2])})[/green]"
    elif detected_models:
        ollama_badge = f"\n[yellow]🟡 Local Ollama Detected on disk: Found {len(detected_models)} models ({', '.join(detected_models[:2])})[/yellow]"

    console.print(Panel.fit(
        f"[bold cyan]🎵 AI Orchestra Setup v2.1[/bold cyan]\n"
        "Configure API keys and models for each orchestra musician."
        f"{ollama_badge}\n"
        "[dim]Tip: You can use Cloud models (Gemini/OpenAI), 100% Local Ollama, or a Hybrid mix![/dim]",
        border_style="yellow"
    ))

    console.print("\n[bold]Select a configuration mode:[/bold]")
    console.print("  [bold green]1[/bold green]) 🎼 Full Orchestra / Hybrid Mode (Choose Cloud or Local Ollama per agent)")
    console.print("  [bold green]2[/bold green]) ⚡ Quick OpenAI Mode (One key, choose model tier)")
    console.print("  [bold green]3[/bold green]) 🔷 Quick Google Gemini Mode (One key, choose model tier)")
    console.print("  [bold green]4[/bold green]) 🚀 Quick Groq Mode (One key, choose model tier)")
    console.print("  [bold green]5[/bold green]) 🦙 Quick Ollama Local Mode ([bold cyan]100% Free, Offline & Unlimited[/bold cyan])")

    default_choice = "5" if (is_active or detected_models) and not existing_search_key else ("3" if "AIzaSy" in existing_search_key else "1")
    choice = Prompt.ask("Choose mode", choices=["1", "2", "3", "4", "5"], default=default_choice)

    if choice == "5":
        # 100% Local Ollama Mode
        console.print("\n[bold green]🦙 Initializing Local Ollama Mode...[/bold green]")
        ensure_ollama_service()
        _, live_models = detect_ollama()
        
        console.print("[dim]Choose an Ollama model for ALL agents:[/dim]")
        chosen_model, base_url = _pick_ollama_model("all agents", live_models)

        config["SEARCH_MODEL"] = chosen_model
        config["SEARCH_API_KEY"] = "ollama"
        config["SEARCH_BASE_URL"] = base_url

        config["SOLVER_MODEL"] = chosen_model
        config["SOLVER_API_KEY"] = "ollama"
        config["SOLVER_BASE_URL"] = base_url

        config["WRITER_MODEL"] = chosen_model
        config["WRITER_API_KEY"] = "ollama"
        config["WRITER_BASE_URL"] = base_url

        config["OLLAMA_BASE_URL"] = base_url

        if len(live_models) > 1 and Confirm.ask("Do you want to assign different local models to each agent?", default=False):
            config["SEARCH_MODEL"], config["SEARCH_BASE_URL"] = _pick_ollama_model("🎻 Searcher", live_models)
            config["SOLVER_MODEL"], config["SOLVER_BASE_URL"] = _pick_ollama_model("🎹 Solver", live_models)
            config["WRITER_MODEL"], config["WRITER_BASE_URL"] = _pick_ollama_model("🎺 Writer", live_models)

    elif choice in ["2", "3", "4"]:
        provider_map = {"2": "openai", "3": "gemini", "4": "groq"}
        label_map = {"2": "OpenAI", "3": "Google Gemini", "4": "Groq"}
        provider = provider_map[choice]
        key = _ask_api_key(f"Enter your {label_map[choice]} API Key", config["SEARCH_API_KEY"])

        console.print("\n[bold]Choose a model tier for ALL agents:[/bold]")
        model = _pick_model_tier(provider, "all agents")

        config["SEARCH_MODEL"] = model
        config["SEARCH_API_KEY"] = key
        config["SEARCH_BASE_URL"] = ""

        config["SOLVER_MODEL"] = model
        config["SOLVER_API_KEY"] = key
        config["SOLVER_BASE_URL"] = ""

        config["WRITER_MODEL"] = model
        config["WRITER_API_KEY"] = key
        config["WRITER_BASE_URL"] = ""

        if Confirm.ask("Do you want to set a different model tier per agent?", default=False):
            config["SEARCH_MODEL"] = _pick_model_tier(provider, "🎻 Searcher")
            config["SOLVER_MODEL"] = _pick_model_tier(provider, "🎹 Solver")
            config["WRITER_MODEL"] = _pick_model_tier(provider, "🎺 Writer")

    else:
        # Full Orchestra / Hybrid Mode: configure each agent individually
        _, live_models = detect_ollama()
        
        def _configure_individual_agent(role_name: str, default_model: str, default_key: str):
            console.print(f"\n[bold cyan]--- {role_name} ---[/bold cyan]")
            console.print("  Select engine:")
            console.print("    [green]1[/green]) 🔷 Google Gemini")
            console.print("    [green]2[/green]) ⚡ OpenAI")
            console.print("    [green]3[/green]) 🚀 Groq")
            console.print("    [green]4[/green]) 🦙 Local Ollama (Free & Offline)")
            
            p_pick = Prompt.ask("  Engine", choices=["1", "2", "3", "4"], default="1")
            if p_pick == "4":
                ensure_ollama_service()
                m_name, b_url = _pick_ollama_model(role_name, live_models)
                return m_name, "ollama", b_url
            else:
                p_map = {"1": "gemini", "2": "openai", "3": "groq"}
                l_map = {"1": "Google Gemini", "2": "OpenAI", "3": "Groq"}
                provider = p_map[p_pick]
                key = _ask_api_key(f"API Key for {l_map[p_pick]}", default_key if not default_key.startswith("ollama") else "")
                model = _pick_model_tier(provider, role_name)
                return model, key, ""

        config["SEARCH_MODEL"], config["SEARCH_API_KEY"], config["SEARCH_BASE_URL"] = _configure_individual_agent(
            "🎻 Part 1: Searcher Agent", config["SEARCH_MODEL"], config["SEARCH_API_KEY"]
        )
        config["SOLVER_MODEL"], config["SOLVER_API_KEY"], config["SOLVER_BASE_URL"] = _configure_individual_agent(
            "🎹 Part 2: Problem Solver Agent", config["SOLVER_MODEL"], config["SOLVER_API_KEY"]
        )
        config["WRITER_MODEL"], config["WRITER_API_KEY"], config["WRITER_BASE_URL"] = _configure_individual_agent(
            "🎺 Part 3: Writer Agent", config["WRITER_MODEL"], config["WRITER_API_KEY"]
        )

    # Optional Search engine key
    console.print("\n[bold cyan]--- 🌐 Web Search Engine API Key (Optional) ---[/bold cyan]")
    console.print("[dim]Press Enter to use the free DuckDuckGo search engine.[/dim]")
    serper = Prompt.ask("Google Serper API Key (Optional)", default=config.get("SERPER_API_KEY", "")).strip()
    config["SERPER_API_KEY"] = serper
    if not serper:
        tavily = Prompt.ask("Tavily Search API Key (Optional)", default=config.get("TAVILY_API_KEY", "")).strip()
        config["TAVILY_API_KEY"] = tavily

    # Confirm saving to .env
    save_env = Confirm.ask("Save these settings to .env for future sessions?", default=True)
    if save_env:
        save_config_to_env(config)
        console.print("[green]✔ Configuration saved successfully to .env[/green]\n")

    return config


# ─── Per-query customization ─────────────────────────────────────────
DEPTH_PROFILES = {
    "fast": {
        "label": "⚡ Fast",
        "search_count": 3,
        "search_instruction": "Perform a quick, focused search. Return only the top 3 most relevant and credible sources.",
        "solve_instruction": "Provide a direct, concise answer. Skip lengthy derivations; focus on the key conclusion.",
        "write_instruction": "Write a short, punchy executive brief (aim for ~300 words). Include only the essential answer, key evidence, and source links.",
    },
    "balanced": {
        "label": "⚖️ Balanced",
        "search_count": 5,
        "search_instruction": "Conduct a thorough multi-source search. Extract 5 credible references with key facts.",
        "solve_instruction": "Analyze step-by-step. Reconcile any conflicting viewpoints using the verified sources.",
        "write_instruction": "Compose a well-structured executive report with Executive Summary, Analysis, Recommendations, and Bibliography.",
    },
    "deep": {
        "label": "🔬 Deep / Exhaustive",
        "search_count": 8,
        "search_instruction": "Perform exhaustive, multi-angle research. Cross-verify findings across 8+ authoritative sources. Include academic papers, official standards, and contrarian viewpoints.",
        "solve_instruction": "Apply rigorous first-principles reasoning. Deconstruct every assumption. Present multi-perspective analysis with formal logical structure. Address edge cases and caveats.",
        "write_instruction": "Author a comprehensive academic-grade analytical dossier. Include detailed comparison tables, formal derivations where applicable, extensive bibliography with annotation, and appendices for supporting data.",
    },
}

def get_query_settings(query: str = "") -> dict:
    """Prompt user for per-query customization: thinking depth, filters, output language with auto-detection."""
    console.print(Panel.fit(
        "[bold cyan]⚙️  Symphony Settings[/bold cyan]\n"
        "[dim]Configure thinking depth, search filters, and output language for this query.[/dim]",
        border_style="yellow"
    ))

    # Auto-detect language from query
    detected_code = detect_language(query) if query else "en"
    detected_code, detected_name = normalize_language(detected_code)

    # 1. Thinking Depth
    console.print("\n[bold]Thinking Depth:[/bold]")
    console.print("  [green]1[/green]) ⚡ Fast         ─ Quick answer, minimal sources, concise report")
    console.print("  [green]2[/green]) ⚖️  Balanced     ─ Standard multi-source analysis & structured report")
    console.print("  [green]3[/green]) 🔬 Deep         ─ Exhaustive academic-grade research & comprehensive dossier")
    depth_choice = Prompt.ask("Depth", choices=["1", "2", "3"], default="2")
    depth_map = {"1": "fast", "2": "balanced", "3": "deep"}
    depth = depth_map[depth_choice]

    # 2. Search Filters
    console.print("\n[bold]Search Filters (Optional — press Enter to skip):[/bold]")
    domain_filter = Prompt.ask("  Restrict to domains (e.g. [dim].com, .edu, nature.com[/dim])", default="").strip()
    language_filter = Prompt.ask("  Source language code  (e.g. [dim]en, pt, fa, de[/dim] or 'all')", default="all").strip()
    if language_filter.lower() == "all":
        language_filter = ""

    # 3. Output Language (with auto-detection default)
    console.print(f"\n[bold]Output Language:[/bold] [dim](Auto-detected from query: [bold green]{detected_name}[/bold green])[/dim]")
    output_language_input = Prompt.ask(
        f"  Report output language (e.g. [dim]fa, en, pt, de[/dim])",
        default=detected_code
    ).strip()

    if not output_language_input or output_language_input.lower() == "auto":
        output_language, out_display = detected_code, detected_name
    else:
        output_language, out_display = normalize_language(output_language_input)

    settings = {
        "depth": depth,
        "depth_profile": DEPTH_PROFILES[depth],
        "domain_filter": domain_filter,
        "language_filter": language_filter,
        "output_language": output_language,
    }

    # Summary
    dp = settings["depth_profile"]
    summary_parts = [f"Depth: {dp['label']}"]
    if domain_filter:
        summary_parts.append(f"Domains: {domain_filter}")
    if language_filter:
        summary_parts.append(f"Source Lang: {language_filter}")
    summary_parts.append(f"Output Lang: {out_display} ({output_language})")
    console.print(f"\n[dim]→ Settings: {' | '.join(summary_parts)}[/dim]")

    return settings
