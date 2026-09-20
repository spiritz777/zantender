"""Prompt loader for tender document analysis."""

from pathlib import Path


ANALYSIS_SYSTEM_INSTRUCTION = (
    Path(__file__).with_name("analysis.txt").read_text(encoding="utf-8").strip()
)
