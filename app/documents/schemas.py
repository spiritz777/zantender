"""Shared document-processing data structures."""

from pathlib import Path

from pydantic import BaseModel, Field


class DocumentPage(BaseModel):
    page_number: int = Field(ge=1)
    text: str


class DocumentChunkData(BaseModel):
    chunk_index: int = Field(ge=0)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    text: str


class ProcessedDocument(BaseModel):
    document_id: int
    filename: str
    file_path: Path
    file_type: str
    page_count: int
    chunks: list[DocumentChunkData]
