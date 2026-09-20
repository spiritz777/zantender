"""Prompt loader for the general procurement consultant."""

from pathlib import Path


CONSULTANT_SYSTEM_INSTRUCTION = (
    Path(__file__).with_name("consultant.txt").read_text(encoding="utf-8").strip()
)
