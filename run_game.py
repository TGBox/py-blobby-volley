#!/usr/bin/env python3
"""Launcher script for Blobby Volley."""

import sys
from pathlib import Path

# Ensure src directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from blobby_volley.main import main

if __name__ == "__main__":
    main()
