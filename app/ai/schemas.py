"""Structured AI responses for document analysis."""

from pydantic import BaseModel, Field


class TenderAnalysisResult(BaseModel):
    title: str = ""
    customer: str = ""
    summary: str
    requirements: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    score: int = Field(ge=0, le=100)
    recommendation: str
