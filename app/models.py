"""
Pydantic data models that define the contracts between frontend, supervisor,
and worker agents. Keeping these in one place makes it easy to evolve schemas
without hunting through the codebase.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FrontendOptions(BaseModel):
    """Flags that the UI can send along with a query."""

    debug: bool = False


class FrontendRequest(BaseModel):
    """Incoming payload from the browser."""

    query: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    options: FrontendOptions = Field(default_factory=FrontendOptions)


class UsedAgentEntry(BaseModel):
    """Compact summary for UI/debug panels."""

    name: str
    intent: str
    status: str


class ErrorModel(BaseModel):
    type: str
    message: str


class OutputModel(BaseModel):
    result: Any
    confidence: Optional[float] = None
    details: Optional[str] = None


class AgentResponse(BaseModel):
    request_id: str
    agent_name: str
    status: str
    output: Optional[OutputModel] = None
    error: Optional[ErrorModel] = None

    def is_success(self) -> bool:
        return self.status == "success" and self.output is not None


class AgentRequest(BaseModel):
    request_id: str
    agent_name: str
    intent: str
    input: Dict[str, Any]
    context: Dict[str, Any]


class AgentMetadata(BaseModel):
    name: str
    description: str
    intents: List[str]
    type: str  # "http" or "cli"
    endpoint: Optional[str] = None
    command: Optional[str] = None
    healthcheck: Optional[str] = None
    timeout_ms: int = 5000


class PlanStep(BaseModel):
    step_id: int
    agent: str
    intent: str
    input_source: str  # "user_query" or "step:X.output.result"


class Plan(BaseModel):
    steps: List[PlanStep]


class SupervisorResponse(BaseModel):
    answer: str
    used_agents: List[UsedAgentEntry]
    intermediate_results: Dict[str, Any]
    error: Optional[ErrorModel] = None
