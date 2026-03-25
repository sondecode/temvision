"""LoL Desktop Overlay - Entry Point.

Usage:
    python lol_overlay.py
    python lol_overlay.py --gui
    python lol_overlay.py --interval 0.5

Starts the OP.GG-style desktop overlay for League of Legends.
"""

import argparse
import logging
import sys


def main():
    parser = argparse.ArgumentParser(
        description="LoL Desktop Overlay - OP.GG style game overlay"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Enable GUI overlay (requires PySide6)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Update interval in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    from temvision.lol.overlay_app import LoLOverlayApp

    app = LoLOverlayApp(
        update_interval=args.interval,
        use_gui=args.gui,
    )

    try:
        app.run()
    except KeyboardInterrupt:
        app.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
