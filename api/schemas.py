# api/schemas.py
from typing import Literal

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    status: str | None = None
    sprint: str | None = None


class SearchResult(BaseModel):
    chunk_id: str
    issue_key: str
    title: str
    chunk_type: str
    text: str
    score: float
    jira_url: str
    status: str | None = None
    sprint: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int


class RagRequest(BaseModel):
    question: str = Field(..., min_length=1)
    history: list[ConversationMessage] = Field(default_factory=list, max_length=20)
    status: str | None = None
    sprint: str | None = None


class Source(BaseModel):
    chunk_id: str
    issue_key: str
    title: str
    chunk_type: str
    jira_url: str
    score: float


class RagResponse(BaseModel):
    answer: str
    sources: list[Source]
