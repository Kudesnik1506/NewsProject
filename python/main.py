"""
NewsProject Orchestrator — sequential pipeline runner.

Usage:
    python main.py                        # USA, today
    python main.py --country USA          # explicit country
    python main.py --date 2026-04-04      # specific date
    python main.py --fast                 # skip verification step
    python main.py --country USA --topic "торговые тарифы"
"""
import argparse
from datetime import date, datetime

from agents import collector, filter_agent, verifier, analyst, reporter


def parse_args():
    parser = argparse.ArgumentParser(description="NewsProject daily digest pipeline")
    parser.add_argument("--country", default="USA", help="Country code (default: USA)")
    parser.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today)")
    parser.add_argument("--fast", action="store_true", help="Skip verification step")
    parser.add_argument("--topic", default=None, help="Optional thematic focus")
    return parser.parse_args()


def run_pipeline(country: str, target_date: date, fast: bool = False, topic: str | None = None) -> str:
    print(f"\n{'='*60}")
    print(f"NewsProject Pipeline — {country} — {target_date}")
    if topic:
        print(f"Topic focus: {topic}")
    if fast:
        print("Mode: FAST (verification skipped)")
    print(f"{'='*60}\n")

    # Step 1: Collect
    raw_articles = collector.run(country, target_date)
    print(f"Step 1 OK  Collected:   {len(raw_articles)} articles\n")

    if not raw_articles:
        print("Pipeline stopped: no articles collected.")
        return ""

    # Step 2: Filter
    filtered = filter_agent.run(raw_articles)
    print(f"Step 2 OK  Filtered:    {len(filtered)} articles\n")

    if not filtered:
        print("Pipeline stopped: no articles after filtering.")
        return ""

    # Step 3: Verify (skip in fast mode)
    if fast:
        for a in filtered:
            a.setdefault("verification_status", "UNVERIFIED")
            a.setdefault("source_count", 1)
            a.setdefault("verification_note", "Verification skipped (fast mode)")
        verified = filtered
        print("Step 3 --  Verification skipped (fast mode)\n")
    else:
        verified = verifier.run(filtered)
        print(f"Step 3 OK  Verified:    {len(verified)} articles\n")

    # Step 4: Analyze
    stories = analyst.run(verified)
    print(f"Step 4 OK  Analyzed:    {len(stories)} stories\n")

    if not stories:
        print("Pipeline stopped: no stories after analysis.")
        return ""

    # Step 5: Report
    total_sources = len(raw_articles)
    verified_count = sum(
        1 for a in verified if a.get("verification_status") == "VERIFIED"
    )
    file_path = reporter.run(stories, country, target_date, total_sources, verified_count)
    print(f"Step 5 OK  Report:      {file_path}\n")

    print(f"{'='*60}")
    print(f"Pipeline complete.")
    print(f"  Sources collected:  {total_sources}")
    print(f"  After filtering:    {len(filtered)}")
    print(f"  Verified:           {verified_count}")
    print(f"  Stories in digest:  {len(stories)}")
    print(f"  Output:             {file_path}")
    print(f"{'='*60}\n")

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
    )
