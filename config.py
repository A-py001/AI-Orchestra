"""
Interactive Configuration Manager for AI Orchestra v2
Handles environment setup, API keys, model tier selection, and advanced customization.
"""
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
from dotenv import load_dotenv, set_key
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

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

def _detect_provider(api_key: str) -> str:
    if not api_key:
        return "openai"
    if api_key.startswith("AIzaSy"):
        return "gemini"
    if api_key.startswith("gsk_"):
        return "groq"
    return "openai"

def load_existing_env():
    if os.path.exists(ENV_FILE):
        load_dotenv(ENV_FILE, override=True)

def show_current_config(config: dict):
    table = Table(title="\U0001f39b\ufe0f Current AI Orchestra Configuration", border_style="cyan")
    table.add_column("Orchestra Role", style="bold yellow")
    table.add_column("AI Model", style="green")
    table.add_column("API Key Status", style="magenta")

    def mask_key(k):
        if not k:
            return "[red]Not Set[/red]"
        if len(k) <= 8:
            return "[green]Configured[/green]"
        return f"[green]{k[:4]}...{k[-4:]}[/green]"

    table.add_row("\U0001f3bb 1. Searcher Agent (Researcher)", config.get("SEARCH_MODEL", "-"), mask_key(config.get("SEARCH_API_KEY", "")))
    table.add_row("\U0001f3b9 2. Problem Solver Agent (Soloist)", config.get("SOLVER_MODEL", "-"), mask_key(config.get("SOLVER_API_KEY", "")))
    table.add_row("\U0001f3ba 3. Writer Agent (Master Scribe)", config.get("WRITER_MODEL", "-"), mask_key(config.get("WRITER_API_KEY", "")))

    search_tool_info = "DuckDuckGo / Free Web Search (Active)"
    if config.get("SERPER_API_KEY"):
        search_tool_info = f"Google Serper ({mask_key(config['SERPER_API_KEY'])})"
    elif config.get("TAVILY_API_KEY"):
        search_tool_info = f"Tavily Search ({mask_key(config['TAVILY_API_KEY'])})"
    table.add_row("\U0001f310 Web Search Engine", search_tool_info, "[blue]Auto Fallback[/blue]")

    console.print(table)

def _pick_model_tier(provider: str, role_label: str) -> str:
    """Let the user pick a model tier (light / balanced / heavy / custom) for a given provider."""
    tiers = MODEL_TIERS.get(provider, MODEL_TIERS["openai"])
    console.print(f"\n[bold]  Select model power for {role_label}:[/bold]")
    console.print(f"    [green]1[/green]) \u26a1 Light / Fast   \u2192 [dim]{tiers['light']}[/dim]")
    console.print(f"    [green]2[/green]) \u2696\ufe0f  Balanced      \u2192 [dim]{tiers['balanced']}[/dim]")
    console.print(f"    [green]3[/green]) \U0001f9e0 Heavy / Pro    \u2192 [dim]{tiers['heavy']}[/dim]")
    console.print(f"    [green]4[/green]) \u270f\ufe0f  Custom (type any model name)")
    tier_choice = Prompt.ask("  Tier", choices=["1", "2", "3", "4"], default="2")
    if tier_choice == "1":
        return tiers["light"]
    elif tier_choice == "3":
        return tiers["heavy"]
    elif tier_choice == "4":
        return Prompt.ask("  Enter custom model name")
    return tiers["balanced"]

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
            set_key(ENV_FILE, k, v)
            os.environ[k] = v

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
        "SOLVER_MODEL": os.environ.get("SOLVER_MODEL", "gemini/gemini-3.8-flash"),
        "SOLVER_API_KEY": existing_solver_key,
        "WRITER_MODEL": os.environ.get("WRITER_MODEL", "gemini/gemini-3.8-flash"),
        "WRITER_API_KEY": existing_writer_key,
        "SERPER_API_KEY": os.environ.get("SERPER_API_KEY", ""),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", ""),
    }

    # Normalize model strings from env if needed
    for model_key in ["SEARCH_MODEL", "SOLVER_MODEL", "WRITER_MODEL"]:
        m = config[model_key]
        if "gemini" in m.lower() and not m.startswith("gemini/"):
            clean_m = m.lower().replace(" ", "-")
            config[model_key] = f"gemini/{clean_m}"

    has_any_keys = bool(config["SEARCH_API_KEY"] and config["SOLVER_API_KEY"] and config["WRITER_API_KEY"])

    if has_any_keys and not force_reconfigure:
        show_current_config(config)
        use_saved = Confirm.ask("Do you want to continue with the current saved configuration?", default=True)
        if use_saved:
            return config

    console.print(Panel.fit(
        "[bold cyan]\U0001f3b5 AI Orchestra Setup[/bold cyan]\n"
        "Configure API keys and models for each orchestra musician.\n"
        "[dim]Tip: You can specify distinct APIs/models for each role or use a single provider.[/dim]",
        border_style="yellow"
    ))

    console.print("\n[bold]Select a configuration mode:[/bold]")
    console.print("  [bold green]1[/bold green]) \U0001f3bc Full Orchestra Mode (Set custom API Key & Model tier for each role)")
    console.print("  [bold green]2[/bold green]) \u26a1 Quick OpenAI Mode (One key, choose model tier)")
    console.print("  [bold green]3[/bold green]) \U0001f537 Quick Google Gemini Mode (One key, choose model tier)")
    console.print("  [bold green]4[/bold green]) \U0001f680 Quick Groq Mode (One key, choose model tier)")

    choice = Prompt.ask("Choose mode", choices=["1", "2", "3", "4"], default="3" if "AIzaSy" in existing_search_key else "1")

    if choice in ["2", "3", "4"]:
        provider_map = {"2": "openai", "3": "gemini", "4": "groq"}
        label_map = {"2": "OpenAI", "3": "Google Gemini", "4": "Groq"}
        provider = provider_map[choice]
        key = _ask_api_key(f"Enter your {label_map[choice]} API Key", config["SEARCH_API_KEY"])

        console.print("\n[bold]Choose a model tier for ALL agents:[/bold]")
        model = _pick_model_tier(provider, "all agents")

        config["SEARCH_MODEL"] = model
        config["SEARCH_API_KEY"] = key
        config["SOLVER_MODEL"] = model
        config["SOLVER_API_KEY"] = key
        config["WRITER_MODEL"] = model
        config["WRITER_API_KEY"] = key

        # Allow per-agent override
        if Confirm.ask("Do you want to set a different model tier per agent?", default=False):
            config["SEARCH_MODEL"] = _pick_model_tier(provider, "\U0001f3bb Searcher")
            config["SOLVER_MODEL"] = _pick_model_tier(provider, "\U0001f3b9 Solver")
            config["WRITER_MODEL"] = _pick_model_tier(provider, "\U0001f3ba Writer")
    else:
        # Full Orchestra Mode: separate APIs
        console.print("\n[bold cyan]--- \U0001f3bb Part 1: Searcher Agent ---[/bold cyan]")
        config["SEARCH_API_KEY"] = _ask_api_key("API Key for Searcher", config["SEARCH_API_KEY"])
        provider = _detect_provider(config["SEARCH_API_KEY"])
        config["SEARCH_MODEL"] = _pick_model_tier(provider, "\U0001f3bb Searcher")

        console.print("\n[bold cyan]--- \U0001f3b9 Part 2: Problem Solver Agent ---[/bold cyan]")
        config["SOLVER_API_KEY"] = _ask_api_key("API Key for Solver", config["SOLVER_API_KEY"] or config["SEARCH_API_KEY"])
        provider = _detect_provider(config["SOLVER_API_KEY"])
        config["SOLVER_MODEL"] = _pick_model_tier(provider, "\U0001f3b9 Solver")

        console.print("\n[bold cyan]--- \U0001f3ba Part 3: Writer Agent ---[/bold cyan]")
        config["WRITER_API_KEY"] = _ask_api_key("API Key for Writer", config["WRITER_API_KEY"] or config["SEARCH_API_KEY"])
        provider = _detect_provider(config["WRITER_API_KEY"])
        config["WRITER_MODEL"] = _pick_model_tier(provider, "\U0001f3ba Writer")

    # Optional Search engine key
    console.print("\n[bold cyan]--- \U0001f310 Web Search Engine API Key (Optional) ---[/bold cyan]")
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
        console.print("[green]\u2714 Configuration saved successfully to .env[/green]\n")

    return config


# ─── Per-query customization ─────────────────────────────────────────
DEPTH_PROFILES = {
    "fast": {
        "label": "\u26a1 Fast",
        "search_count": 3,
        "search_instruction": "Perform a quick, focused search. Return only the top 3 most relevant and credible sources.",
        "solve_instruction": "Provide a direct, concise answer. Skip lengthy derivations; focus on the key conclusion.",
        "write_instruction": "Write a short, punchy executive brief (aim for ~300 words). Include only the essential answer, key evidence, and source links.",
    },
    "balanced": {
        "label": "\u2696\ufe0f Balanced",
        "search_count": 5,
        "search_instruction": "Conduct a thorough multi-source search. Extract 5 credible references with key facts.",
        "solve_instruction": "Analyze step-by-step. Reconcile any conflicting viewpoints using the verified sources.",
        "write_instruction": "Compose a well-structured executive report with Executive Summary, Analysis, Recommendations, and Bibliography.",
    },
    "deep": {
        "label": "\U0001f52c Deep / Exhaustive",
        "search_count": 8,
        "search_instruction": "Perform exhaustive, multi-angle research. Cross-verify findings across 8+ authoritative sources. Include academic papers, official standards, and contrarian viewpoints.",
        "solve_instruction": "Apply rigorous first-principles reasoning. Deconstruct every assumption. Present multi-perspective analysis with formal logical structure. Address edge cases and caveats.",
        "write_instruction": "Author a comprehensive academic-grade analytical dossier. Include detailed comparison tables, formal derivations where applicable, extensive bibliography with annotation, and appendices for supporting data.",
    },
}

def get_query_settings() -> dict:
    """Prompt user for per-query customization: thinking depth, filters, output language."""
    console.print(Panel.fit(
        "[bold cyan]\u2699\ufe0f  Symphony Settings[/bold cyan]\n"
        "[dim]Configure thinking depth, search filters, and output language for this query.[/dim]",
        border_style="yellow"
    ))

    # 1. Thinking Depth
    console.print("\n[bold]Thinking Depth:[/bold]")
    console.print("  [green]1[/green]) \u26a1 Fast         \u2500 Quick answer, minimal sources, concise report")
    console.print("  [green]2[/green]) \u2696\ufe0f  Balanced     \u2500 Standard multi-source analysis & structured report")
    console.print("  [green]3[/green]) \U0001f52c Deep         \u2500 Exhaustive academic-grade research & comprehensive dossier")
    depth_choice = Prompt.ask("Depth", choices=["1", "2", "3"], default="2")
    depth_map = {"1": "fast", "2": "balanced", "3": "deep"}
    depth = depth_map[depth_choice]

    # 2. Search Filters
    console.print("\n[bold]Search Filters (Optional \u2014 press Enter to skip):[/bold]")
    domain_filter = Prompt.ask("  Restrict to domains (e.g. [dim].com, .edu, nature.com[/dim])", default="").strip()
    language_filter = Prompt.ask("  Source language code  (e.g. [dim]en, pt, fa, de[/dim] or 'all')", default="all").strip()
    if language_filter.lower() == "all":
        language_filter = ""

    # 3. Output Language
    output_language = Prompt.ask("  Report output language (e.g. [dim]en, fa, pt[/dim])", default="en").strip()

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
    summary_parts.append(f"Output Lang: {output_language}")
    console.print(f"\n[dim]\u2192 Settings: {' | '.join(summary_parts)}[/dim]")

    return settings
