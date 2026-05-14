from pydantic import BaseModel
from typing import Optional, Dict, Any


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str
    policy_source: str  # RBAC / ABAC / RULE_ENGINE
    context: Dict[str, Any] = {}