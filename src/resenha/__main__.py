"""Entry point for Resenha: schedule or single-run."""

import argparse
import asyncio
import logging
import sys

from resenha.config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="resenha")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--schedule", action="store_true", help="Start the scheduler")
    group.add_argument("--once", type=str, metavar="STYLE",
                       choices=["pre-market", "eod", "long-form"],
                       help="Run pipeline once and exit")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    settings = Settings()  # type: ignore[call-arg]

    if args.schedule:
        from resenha.scheduler import ResenhaScheduler
        scheduler = ResenhaScheduler(settings)
        try:
            asyncio.run(scheduler.start())
        except KeyboardInterrupt:
            print("\nShutting down...")
            sys.exit(0)
    else:
        from resenha.pipeline import run_pipeline
        asyncio.run(run_pipeline(settings, args.once))


if __name__ == "__main__":
    main()
