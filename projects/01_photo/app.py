"""Streamlit entry point for the Photo Process Analysis Workbench."""

from pathlib import Path
import os
import sys

PROJECT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / "outputs" / ".matplotlib-cache"))
sys.path.insert(0, str(PROJECT / "scripts"))

from workbench_ui import run  # noqa: E402


run(PROJECT)
