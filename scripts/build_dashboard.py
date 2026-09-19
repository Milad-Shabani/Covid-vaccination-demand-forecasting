#!/usr/bin/env python3
"""Build dashboard/dist/index.html (and docs/index.html for GitHub Pages)."""
import subprocess
import sys
import os

BASE = os.path.join(os.path.dirname(__file__), "..")

if __name__ == "__main__":
    script = os.path.join(BASE, "dashboard", "build_dashboard.py")
    sys.exit(subprocess.call([sys.executable, script]))
