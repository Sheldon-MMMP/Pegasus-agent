from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from agent_server.db import get_db
from agent_server.models import Skill
from agent_server.schemas import CreateSkillRequest, ListSkillsResponse, SkillDTO, SkillStatus, GetSkillResponse
from pathlib import Path

from agent_server.routers.errors import raise_http_error_from_service_error
from agent_server.services.exceptions import ServiceError
from agent_server.services.skills import create_skill as create_skill_service

router = APIRouter(prefix="/api/skills", tags=["skills"])

DbSession = Annotated[Session, Depends(get_db)]

def resolve_skill_path(file_path: str) -> Path:
    return Path.cwd() / file_path


def skill_to_dto(skill: Skill) -> SkillDTO:
    return SkillDTO(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        file_path=skill.file_path,
        content_hash=skill.content_hash,
        status=skill.status,
        version=skill.version,
        source_run_id=skill.source_run_id,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        last_checked_at=skill.last_checked_at,
    )

@router.get("", response_model=ListSkillsResponse)
def list_skills(db: DbSession) -> ListSkillsResponse:
    skills = db.scalars(
        select(Skill).order_by(Skill.updated_at.desc())
    ).all()

    return ListSkillsResponse(
        skills=[skill_to_dto(skill) for skill in skills]
    )


@router.get("/{skill_id}", response_model=GetSkillResponse)
def get_skill(skill_id: UUID, db: DbSession) -> GetSkillResponse:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found.")

    path = resolve_skill_path(skill.file_path)

    if not path.exists():
        if skill.status != SkillStatus.disabled.value:
            skill.status = SkillStatus.missing.value
            db.commit()
            db.refresh(skill)

        return GetSkillResponse(
            skill=skill_to_dto(skill),
            content=None,
        )

    content = path.read_text(encoding="utf-8")

    return GetSkillResponse(
        skill=skill_to_dto(skill),
        content=content,
    )

@router.post("", response_model=SkillDTO)
def create_skill(request: CreateSkillRequest,db: DbSession) -> SkillDTO:
    try:
        skill = create_skill_service(db=db, request=request)
    except ServiceError as exc:
        raise_http_error_from_service_error(exc)

    return skill_to_dto(skill)
