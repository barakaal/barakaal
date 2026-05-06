from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models.agent import AgentType, TaskPriority


class AgentCreate(BaseModel):
    name: str
    agent_type: AgentType
    department_id: Optional[int] = None
    role_description: str
    objectives: List[str] = []
    permissions: List[str] = []
    tools: List[str] = []
    config: Dict[str, Any] = {}


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    agent_type: Optional[AgentType] = None
    department_id: Optional[int] = None
    role_description: Optional[str] = None
    objectives: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    is_active: Optional[bool] = None
    memory_summary: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class AgentOut(BaseModel):
    id: int
    name: str
    agent_type: str
    department_id: Optional[int] = None
    role_description: str
    objectives: List[str]
    permissions: List[str]
    tools: List[str]
    status: str
    is_active: bool
    memory_summary: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentTaskCreate(BaseModel):
    agent_id: int
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    input_data: Dict[str, Any] = {}


class AgentTaskOut(BaseModel):
    id: int
    agent_id: int
    title: str
    description: str
    status: str
    priority: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentDecisionOut(BaseModel):
    id: int
    agent_id: int
    task_id: Optional[int] = None
    decision_type: str
    title: str
    rationale: str
    data_used: Dict[str, Any]
    risk_level: str
    recommendation: str
    estimated_cost_usd: Optional[float] = None
    estimated_revenue_usd: Optional[float] = None
    status: str
    requires_human_approval: bool
    approved_by_user_id: Optional[int] = None
    approval_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalAction(BaseModel):
    status: str
    review_notes: Optional[str] = None
