"""
NewsProject Orchestrator — sequential pipeline runner.

Usage:
    python main.py                        # USA, today
    python main.py --country USA          # explicit country
    python main.py --date 2026-04-04      # specific date
    python main.py --fast                 # skip verification step
    python main.py --country USA --topic "торговые тарифы"
    python main.py --days 7               # weekly digest (last 7 days)
"""
import argparse
import time
from datetime import date, datetime, timedelta

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agents import collector, triage_agent, analyst, paei_classifier, reporter

console = Console(highlight=False, legacy_windows=False)


def parse_args():
    """Разбирает аргументы командной строки: страна, дата, быстрый режим, тематический фокус, глубина."""
    parser = argparse.ArgumentParser(description="NewsProject daily digest pipeline")
    parser.add_argument("--country", default="USA", help="Country code (default: USA)")
    parser.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today)")
    parser.add_argument("--fast", action="store_true", help="Skip verification step")
    parser.add_argument("--topic", default=None, help="Optional thematic focus")
    parser.add_argument("--days", type=int, default=1, help="Number of days to cover (default: 1)")
    return parser.parse_args()


def _step(label: str, fn):
    """Запускает fn() со спиннером, возвращает (result, elapsed_seconds)."""
    t0 = time.time()
    with console.status(f"[cyan]{label}[/cyan]", spinner="dots"):
        result = fn()
    return result, time.time() - t0


def run_pipeline(
    country: str,
    target_date: date,
    fast: bool = False,
    topic: str | None = None,
    days: int = 1,
) -> str:
    """Запускает полный пайплайн из 6 шагов и возвращает путь к готовому дайджесту."""
    date_from = target_date - timedelta(days=days - 1) if days > 1 else None
    pipeline_start = time.time()

    # ── Header ─────────────────────────────────────────────────────────────
    if date_from:
        period = f"{date_from} – {target_date}  ({days} дней)"
    else:
        period = str(target_date)
    subtitle = f"[yellow]FAST[/yellow]  " if fast else ""
    if topic:
        subtitle += f"[dim]Тема: {topic}[/dim]"
    console.print()
    console.print(Panel(
        f"[bold]{country}[/bold]  ·  {period}\n{subtitle}".strip(),
        title="[bold blue]NewsProject[/bold blue]",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
    console.print()

    log: list[tuple[str, str, float]] = []  # (name, summary, elapsed)

    # ── Step 1: Collect ────────────────────────────────────────────────────
    raw_articles, t = _step(
        "Step 1/6  Сбор новостей...",
        lambda: collector.run(country, target_date, date_from=date_from),
    )
    console.print(f"  [green]✓[/green]  [bold]Шаг 1[/bold]  Collect    [cyan]{len(raw_articles):>4}[/cyan] статей    [dim]{t:.1f}s[/dim]")
    log.append(("Collect", f"{len(raw_articles)} статей", t))

    if not raw_articles:
        console.print("\n  [red]Остановка: нет статей после сбора.[/red]")
        return ""

    # ── Step 2: Triage (scoring + verification) ────────────────────────────
    triaged, t = _step(
        "Step 2/5  Отбор и верификация...",
        lambda: triage_agent.run(raw_articles, verify=not fast),
    )
    v_ok  = sum(1 for a in triaged if a.get("verification_status") == "VERIFIED")
    v_no  = sum(1 for a in triaged if a.get("verification_status") == "UNVERIFIED")
    v_dis = sum(1 for a in triaged if a.get("verification_status") == "DISPUTED")
    console.print(
        f"  [green]✓[/green]  [bold]Шаг 2[/bold]  Triage     "
        f"[cyan]{len(triaged):>4}[/cyan] статей  "
        f"[green]{v_ok}✓[/green] [yellow]{v_no}?[/yellow] [red]{v_dis}✗[/red]  [dim]{t:.1f}s[/dim]"
    )
    log.append(("Triage", f"{len(triaged)} статей  {v_ok}✓ {v_no}? {v_dis}✗", t))

    verified = [a for a in triaged if a.get("verification_status") != "DISPUTED"]
    verified_count = v_ok

    if not verified:
        console.print("\n  [red]Остановка: нет статей после отбора.[/red]")
        return ""

    # ── Step 3: Analyze ────────────────────────────────────────────────────
    stories, t = _step(
        "Step 3/5  Геостратегический анализ...",
        lambda: analyst.run(verified, country),
    )
    console.print(f"  [green]✓[/green]  [bold]Шаг 3[/bold]  Analyze    [cyan]{len(stories):>4}[/cyan] историй   [dim]{t:.1f}s[/dim]")
    log.append(("Analyze", f"{len(stories)} историй", t))

    if not stories:
        console.print("\n  [red]Остановка: нет историй после анализа.[/red]")
        return ""

    # ── Step 4: PAEI Classify ──────────────────────────────────────────────
    state_diagnosis, t = _step(
        "Step 4/5  Диагноз PAEI×Jung...",
        lambda: paei_classifier.run(stories, country),
    )
    dominant = state_diagnosis.get("dominant", []) if state_diagnosis else []
    deficit = state_diagnosis.get("deficit", []) if state_diagnosis else []
    console.print(
        f"  [green]✓[/green]  [bold]Шаг 4[/bold]  PAEI       "
        f"dominant=[cyan]{', '.join(dominant) or '—'}[/cyan]  deficit=[yellow]{', '.join(deficit) or '—'}[/yellow]  [dim]{t:.1f}s[/dim]"
    )
    log.append(("PAEI", f"dom: {', '.join(dominant) or '—'}", t))

    # ── Step 5: Report ─────────────────────────────────────────────────────
    total_sources = len(raw_articles)

    file_path, t = _step(
        "Step 5/5  Генерация дайджеста...",
        lambda: reporter.run(
            stories, state_diagnosis, country, target_date,
            total_sources, verified_count, date_from=date_from,
        ),
    )
    console.print(f"  [green]✓[/green]  [bold]Шаг 5[/bold]  Report     [green]сохранён[/green]   [dim]{t:.1f}s[/dim]")
    log.append(("Report", "сохранён", t))

    # ── Summary ────────────────────────────────────────────────────────────
    total_time = time.time() - pipeline_start
    console.print()

    tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    tbl.add_column("шаг", style="bold")
    tbl.add_column("результат", style="cyan")
    tbl.add_column("время", style="dim", justify="right")
    for name, summary, elapsed in log:
        tbl.add_row(name, summary, f"{elapsed:.1f}s")

    console.print(Panel(
        tbl,
        title="[bold green]Pipeline завершён[/bold green]",
        subtitle=f"[dim]Всего: {total_time:.0f}s[/dim]",
        box=box.ROUNDED,
        padding=(0, 1),
    ))
    console.print(f"\n  [dim]Файл:[/dim] [bold]{file_path}[/bold]\n")

    return file_path


if __name__ == "__main__":
    args = parse_args()

    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today()

    run_pipeline(
        country=args.country,
        target_date=target_date,
        fast=args.fast,
        topic=args.topic,
        days=args.days,
    )
