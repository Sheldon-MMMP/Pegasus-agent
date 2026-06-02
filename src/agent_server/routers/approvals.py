from uuid import UUID

from fastapi import APIRouter

from agent_server.schemas import ResolveApprovalRequest, ResolveApprovalResponse
from agent_server.services.approvals import resolve_approval as resolve_approval_service

router = APIRouter(prefix="/api/tool-approvals", tags=["approvals"])


@router.post("/{approval_id}", response_model=ResolveApprovalResponse)
def resolve_approval(
    approval_id: UUID,
    request: ResolveApprovalRequest,
) -> ResolveApprovalResponse:
    return resolve_approval_service(approval_id, request)
