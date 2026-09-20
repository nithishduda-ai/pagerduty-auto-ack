#!/usr/bin/env python3
"""Backward-compatible entry point for the pd-auto-ack CLI."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from pagerduty_auto_ack.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
