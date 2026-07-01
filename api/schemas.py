# api/schemas.py
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
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
    status: str
    sprint: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int


class RagRequest(BaseModel):
    question: str = Field(..., min_length=1)
    history: list[ConversationMessage] = Field(default_factory=list)
    status: str | None = None
    sprint: str | None = None


class Source(BaseModel):
    chunk_id: str
    issue_key: str
    title: str
    chunk_type: str
    jira_url: str
    score: float
