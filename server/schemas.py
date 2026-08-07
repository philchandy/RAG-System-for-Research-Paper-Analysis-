"""
Pydantic request/response models mirroring the rag pipeline dicts.
"""

from typing import Literal

from pydantic import BaseModel, Field


class FirstChunk(BaseModel):
    section: str
    text_preview: str


class IndexReport(BaseModel):
    document_id: str
    source: str
    character_count: int
    chunk_count: int
    first_chunk: FirstChunk | None = None


class UploadResponse(BaseModel):
    status: str
    report: IndexReport


class DocumentInfo(BaseModel):
    document_id: str
    source: str | None = None
    chunk_count: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]


class DeleteResponse(BaseModel):
    document_id: str
    removed_chunks: int
    file_deleted: bool
    source: str | None = None


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    document_ids: list[str] | None = None
    top_k: int = Field(default=3, ge=1, le=20)
    answer_mode: Literal["extractive", "openai"] = "extractive"


class EvidenceItem(BaseModel):
    chunk_id: str
    document_id: str | None = None
    source: str | None = None
    section: str | None = None
    text: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    answer_mode: str
    filtered_document_ids: list[str]
    evidence: list[EvidenceItem]


class SummarizeRequest(BaseModel):
    document_ids: list[str] | None = None
    top_k: int = Field(default=3, ge=1, le=20)
    answer_mode: Literal["extractive", "openai"] = "extractive"


class SummaryField(BaseModel):
    question: str
    answer: str
    evidence: list[EvidenceItem]


class SummarizeResponse(BaseModel):
    answer_mode: str
    filtered_document_ids: list[str]
    summary: dict[str, SummaryField]
