"""
Pydantic request/response models mirroring the rag pipeline dicts.
"""

from pydantic import BaseModel


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
