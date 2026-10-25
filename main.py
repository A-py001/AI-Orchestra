"""
AI Orchestra MVP v2
Main Interactive Terminal Application
With Thinking Depth, Model Tier Selection, and Custom Stage Filters.
"""
import sys
import os

# Disable CrewAI telemetry to avoid connection timeouts
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.table import Table

from config import get_orchestra_config, show_current_config, get_query_settings
from orchestra import AIOrchestra

console = Console()

BANNER_ART = """[bold cyan]
   \u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557     \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2557  \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2557 
  \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551    \u2588\u2588\u2554\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2588\u2588\u2554\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557
  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2551    \u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551     \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557   \u2588\u2588\u2551   \u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551
  \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2551    \u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551     \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u255d  \u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551   \u2588\u2588\u2551   \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551
  \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551    \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551  \u2588\u2588\u2551\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551   \u2588\u2588\u2551   \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551
  \u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d     \u255a\u2550\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u255d  \u255a\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d   \u255a\u2550\u255d   \u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d
[/bold cyan]
[bold magenta]           \U0001f3bc Multi-Agent AI Orchestra v2 powered by CrewAI \U0001f3bc[/bold magenta]
"""

def print_welcome():
    console.print(BANNER_ART)
    intro_table = Table(title="\U0001f465 AI Orchestra Roles & Instruments", border_style="bright_blue")
    intro_table.add_column("Instrument / Role", style="bold yellow", width=26)
    intro_table.add_column("Symphony Mission", style="white")
    intro_table.add_column("Input \u27a1 Output", style="green")

    intro_table.add_row(
        "\U0001f3bb First Violin (Researcher)",
        "Scour the web for authoritative articles, official docs & empirical evidence",
        "User Query \u27a1 Verified Sources & Facts"
    )
    intro_table.add_row(
        "\U0001f3b9 Soloist (Problem Solver)",
        "Deep first-principles reasoning, evidence synthesis & rigorous problem-solving",
        "Verified Sources \u27a1 Proven Analytical Solution"
    )
    intro_table.add_row(
        "\U0001f3ba Master Scribe (Writer)",
        "Compose an eloquent, publication-ready executive report with bibliography",
        "Solution & Sources \u27a1 Formatted Executive Dossier"
    )

    console.print(intro_table)
    console.print()

def main():
    parser = argparse.ArgumentParser(description="AI Orchestra v2 - Multi-Agent System with CrewAI")
    parser.add_argument("--reconfigure", action="store_true", help="Reconfigure API keys and models")
    parser.add_argument("--query", type=str, default=None, help="Directly execute a query without interactive loop")
    parser.add_argument("--depth", type=str, choices=["fast", "balanced", "deep"], default=None, help="Thinking depth for --query mode")
    parser.add_argument("--lang", type=str, default=None, help="Output language for --query mode (e.g. 'fa', 'en', 'es')")
    args = parser.parse_args()

    print_welcome()

    # 1. Configuration Phase
    config = get_orchestra_config(force_reconfigure=args.reconfigure)

    # 2. Check if at least one API key is present
    if not config.get("SEARCH_API_KEY") and not config.get("SOLVER_API_KEY"):
        console.print("[bold red]\u274c Error: At least one AI API key is required to start the Orchestra.[/bold red]")
        sys.exit(1)

    console.print("\n[bold green]\U0001f3bb The Conductor is tuning instruments and assembling musicians...[/bold green]\n")
    try:
        orchestra = AIOrchestra(config)
    except Exception as e:
        console.print(f"[bold red]\u274c Error initializing AI Orchestra: {e}[/bold red]")
        sys.exit(1)

    # 3. Execution Phase
    if args.query:
        from config import DEPTH_PROFILES
        from tools.language_detector import detect_language
        depth = args.depth or "balanced"
        lang = args.lang if args.lang else detect_language(args.query.strip())
        settings = {
            "depth": depth,
            "depth_profile": DEPTH_PROFILES[depth],
            "domain_filter": "",
            "language_filter": "",
            "output_language": lang,
        }
        run_orchestra_query(orchestra, args.query.strip(), settings)
        return

    while True:
        console.print(Panel(
            "[bold cyan]Enter your question, challenge, or research topic:[/bold cyan]\n"
            "[dim](Type 'config' to adjust settings/keys, or 'exit' / 'q' to quit)[/dim]",
            border_style="cyan"
        ))

        query = Prompt.ask("[bold yellow]Your Challenge[/bold yellow]").strip()

        if not query:
            continue

        if query.lower() in ["exit", "quit", "q"]:
            console.print("[bold cyan]\U0001f44b Thank you for performing with the AI Orchestra. Farewell![/bold cyan]")
            break

        if query.lower() in ["config", "setup"]:
            config = get_orchestra_config(force_reconfigure=True)
            orchestra = AIOrchestra(config)
            continue

        # Get per-query settings (depth, filters, output language)
        settings = get_query_settings(query)

        run_orchestra_query(orchestra, query, settings)

        console.print("\n" + "\u2500" * 70 + "\n")
        again = Confirm.ask("Would you like the Orchestra to tackle another challenge?", default=True)
        if not again:
            console.print("[bold cyan]\U0001f44b The Symphony has concluded. Goodbye![/bold cyan]")
            break

def run_orchestra_query(orchestra: AIOrchestra, query: str, settings: dict):
    depth_label = settings.get("depth_profile", {}).get("label", "Balanced")
    console.print(f"\n[bold magenta]\U0001f3bc Commencing Symphony for Query:[/bold magenta] [yellow]\u00ab{query}\u00bb[/yellow]")
    console.print(f"[dim]Thinking Depth: {depth_label}[/dim]")
    domain = settings.get("domain_filter", "")
    lang = settings.get("language_filter", "")
    out_lang = settings.get("output_language", "en")
    if domain or lang:
        filter_parts = []
        if domain:
            filter_parts.append(f"Domains: {domain}")
        if lang:
            filter_parts.append(f"Source Lang: {lang}")
        console.print(f"[dim]Filters: {' | '.join(filter_parts)}[/dim]")
    console.print(f"[dim]Output Language: {out_lang}[/dim]")
    console.print("[dim]The 3 agents will perform sequentially: Researcher \u27a1 Problem Solver \u27a1 Master Scribe...[/dim]\n")

    try:
        with console.status("[bold green]\U0001f3b5 The Orchestra is performing... Please wait...[/bold green]", spinner="dots"):
            output_text, filepath, elapsed = orchestra.perform_symphony(query, settings)

        console.print("\n" + "\u2550" * 75)
        console.print(Panel(
            f"[bold green]\u2728 Symphony Performance Completed Successfully![/bold green]\n"
            f"[bold]\u23f1 Duration:[/bold] {elapsed:.2f} seconds\n"
            f"[bold]\U0001f4c1 Report Saved To:[/bold] [cyan]{filepath}[/cyan]",
            border_style="green",
            title="\U0001f3c1 AI Symphony Result"
        ))
        console.print("\u2550" * 75 + "\n")

        console.print(Markdown(output_text))

        console.print(f"\n[green]\u2714 Full executive report saved to:[/green] [underline cyan]{filepath}[/underline cyan]")

    except Exception as e:
        console.print(f"\n[bold red]\u274c An error occurred during the orchestra execution:[/bold red] {e}")
        console.print("[dim]Please verify your API keys, network connection, or selected model names.[/dim]")

if __name__ == "__main__":
    main()
