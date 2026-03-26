"""Compatibility wrapper for legacy LoL overlay entrypoint.

Preferred usage:
    python main.py --game=lol
"""

from __future__ import annotations

import warnings
import sys

from main import main as temvision_main


if __name__ == "__main__":
    warnings.warn(
        "`python lol_overlay.py` is deprecated. "
        "Please use `python main.py --game=lol`.",
        DeprecationWarning,
        stacklevel=1,
    )
    if "--game" not in sys.argv:
        sys.argv = [sys.argv[0], "--game=lol", *sys.argv[1:]]
    temvision_main()
