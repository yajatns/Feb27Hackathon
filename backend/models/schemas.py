"""Pydantic schemas for request/response models."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class HireRequestCreate(BaseModel):
    employee_name: str = Field(..., examples=["Sarah Chen"])
    role: str = Field(..., examples=["Senior Engineer"])
    department: str = Field(..., examples=["Engineering"])
    salary: float = Field(..., examples=[150000.0])
    location: str = Field(..., examples=["San Francisco, CA"])
    start_date: str = Field(..., examples=["2026-03-01"])


class AgentTaskResponse(BaseModel):
    id: uuid.UUID
    agent_name: str
    tool_used: str
    input_data: str | None = None
    output_data: str | None = None
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    model_config = {"from_attributes": True}


class HireRequestResponse(BaseModel):
    id: uuid.UUID
    employee_name: str
    role: str
    department: str
    salary: float
    location: str
    start_date: str
    status: str
    reasoning_summary: str | None = None
    created_at: datetime
    tasks: list[AgentTaskResponse] = []
    model_config = {"from_attributes": True}


class QueryRequest(BaseModel):
    message: str = Field(..., examples=["Hire Sarah Chen as Senior Engineer at $150K"])
    session_id: str | None = Field(None, description="Chat session ID for conversation persistence")


class QueryResponse(BaseModel):
    response: str
    tools_used: list[str] = []
    reasoning: str | None = None
    hire_request_id: str | None = None


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    properties: dict = {}


class GraphResponse(BaseModel):
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []


class AgentStatus(BaseModel):
    name: str
    status: str
    current_task: str | None = None
    last_active: datetime | None = None


class PipelineStatus(BaseModel):
    hire_request_id: str | None = None
    overall_status: str
    agents: list[AgentStatus] = []
    progress_pct: float = 0.0


class HealthResponse(BaseModel):
    status: str = "healthy"
    database: str = "connected"
    neo4j: str = "connected"
    version: str = "0.1.0"


class WSMessage(BaseModel):
    type: str
    data: dict = {}


class UserOverrideCreate(BaseModel):
    hire_request_id: uuid.UUID
    field_overridden: str
    new_value: str
    reason: str | None = None


class UserOverrideResponse(BaseModel):
    id: uuid.UUID
    hire_request_id: uuid.UUID
    field_overridden: str
    original_value: str | None = None
    new_value: str
    reason: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class CronResultResponse(BaseModel):
    id: uuid.UUID
    cron_type: str
    findings: str
    recommendations: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}
