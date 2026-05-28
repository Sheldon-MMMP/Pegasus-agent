from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter

from agent_server.schemas import CreateSkillRequest, ListSkillsResponse, SkillDTO
from agent_server.state import skills_state

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=ListSkillsResponse)
def list_skills() -> ListSkillsResponse:
    return ListSkillsResponse(skills=skills_state)


@router.post("", response_model=SkillDTO)
def create_skill(request: CreateSkillRequest) -> SkillDTO:
    now = datetime.now(UTC)

    skill = SkillDTO(
        id=uuid4(),
        name=request.name,
        description=request.description,
        content=request.content,
        version=1,
        source_run_id=None,
        created_at=now,
        updated_at=now,
    )

    skills_state.append(skill)

    return skill
