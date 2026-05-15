import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from omnibioai_iam_client.client import AsyncIAMClient
from audit.logger import AuditLogger
from audit.models import AuditEvent


class PolicyEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Zero-trust enforcement middleware for OmniBioAI.

    Flow:
    Request → IAM validation → Policy evaluation → Audit → Allow/Deny
    """

    def __init__(
        self,
        app,
        iam_client: AsyncIAMClient,
        policy_client,
        audit_logger: AuditLogger,
        jwt_secret: str,
    ):
        super().__init__(app)
        self.iam = iam_client
        self.policy = policy_client
        self.audit = audit_logger
        self.jwt_secret = jwt_secret

    async def dispatch(self, request, call_next):
        start_time = time.time()

        # ---------------------------------
        # 1. Extract token
        # ---------------------------------
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse({"error": "Missing token"}, status_code=401)

        token = auth_header.replace("Bearer ", "")

        # ---------------------------------
        # 2. IAM validation (cached + fast path)
        # ---------------------------------
        user = await self.iam.get_user(token, self.jwt_secret)

        if not user:
            await self.audit.log(
                AuditEvent(
                    service="gateway",
                    event_type="auth_failed",
                    user_id=None,
                    action="request_blocked",
                    decision="deny",
                    reason="invalid_token",
                )
            )
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        # attach user to request
        request.state.user = user

        # ---------------------------------
        # 3. Policy evaluation
        # ---------------------------------
        policy_decision = await self.policy.evaluate(
            user=user,
            path=str(request.url.path),
            method=request.method,
            headers=dict(request.headers),
        )

        # ---------------------------------
        # 4. Deny path
        # ---------------------------------
        if not policy_decision["allow"]:
            await self.audit.log(
                AuditEvent(
                    service="policy-engine",
                    event_type="policy_decision",
                    user_id=user.user_id,
                    action=f"{request.method} {request.url.path}",
                    decision="deny",
                    reason=policy_decision.get("reason", "policy_block"),
                )
            )

            return JSONResponse(
                {
                    "error": "Access denied",
                    "reason": policy_decision.get("reason"),
                },
                status_code=403,
            )

        # ---------------------------------
        # 5. Allow path
        # ---------------------------------
        response = await call_next(request)

        # ---------------------------------
        # 6. Audit success
        # ---------------------------------
        await self.audit.log(
            AuditEvent(
                service="policy-engine",
                event_type="policy_decision",
                user_id=user.user_id,
                action=f"{request.method} {request.url.path}",
                decision="allow",
                reason="policy_pass",
                context={
                    "latency_ms": int((time.time() - start_time) * 1000),
                },
            )
        )

        return response