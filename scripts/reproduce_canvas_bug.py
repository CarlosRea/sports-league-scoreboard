#!/usr/bin/env python3
"""
Convenience entrypoint pointing to on-call-engineer/reproduce_canvas_bug.py.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
on_call_dir = root_dir / "on-call-engineer"
if str(on_call_dir) not in sys.path:
    sys.path.insert(0, str(on_call_dir))

from reproduce_canvas_bug import main  # noqa: E402

if __name__ == "__main__":
    main()
