from pydantic import BaseModel
from typing import Dict, Any, Optional


class PolicyRequest(BaseModel):
    user_id: str
    email: Optional[str] = None
    roles: list[str] = []
    permissions: list[str] = []

    action: str
    resource: str

    context: Dict[str, Any] = {}