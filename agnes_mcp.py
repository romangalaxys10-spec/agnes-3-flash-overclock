#!/usr/bin/env python3
"""Entry point for hosts: `python3 /abs/path/agnes_mcp.py` works from any working directory."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agnes_kit.mcp_server import main

if __name__ == "__main__":
    sys.exit(main())
