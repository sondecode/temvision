"""Temvision - AI Vision Framework for Real-Time Game Decision Support.

Usage:
    python main.py --game=lol
    python main.py --game=lol --gui
    python main.py --game=lol --llm
"""

from __future__ import annotations

import argparse
import logging
import sys


def main() -> None:
    """Main entry point for Temvision."""
    parser = argparse.ArgumentParser(
        description="Temvision - AI Vision Framework for Real-Time Game Decision Support"
    )
    parser.add_argument(
        "--game",
        type=str,
        required=True,
        help="Game identifier (e.g., lol, valorant)",
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default="config",
        help="Path to config directory (default: config)",
    )
    parser.add_argument(
        "--skills-dir",
        type=str,
        default="skills",
        help="Path to skills directory (default: skills)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Enable GUI overlay (requires PySide6)",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM-based decision making",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        from temvision.app import TemvisionApp

        app = TemvisionApp(
            game=args.game,
            config_dir=args.config_dir,
            skills_dir=args.skills_dir,
            use_gui=args.gui,
            use_llm=args.llm,
        )
        app.run()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopped")


if __name__ == "__main__":
    main()
