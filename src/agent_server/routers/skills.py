import hashlib
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, exists
from sqlalchemy.orm import Session

from agent_server.db import get_db
from agent_server.models import Skill
from agent_server.schemas import CreateSkillRequest, ListSkillsResponse, SkillDTO, SkillStatus, GetSkillResponse
from pathlib import Path

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
    now = datetime.now(UTC)

    is_exist = db.scalar(select(exists().where(Skill.name == request.name)))

    if is_exist:
        raise HTTPException(status_code=409, detail="Skill is already created.")

    skill_file_path = Path.cwd() / ".skills" / request.name / "SKILL.md"

    if skill_file_path.exists():
        raise HTTPException(status_code=409, detail="Skill directory already exists.")

    skill_content = f"""---
name: {request.name}
description: {request.description}
version: 1
---

{request.content}
"""

    skill_file_path.parent.mkdir(parents=True, exist_ok=False)
    skill_file_path.write_text(skill_content, encoding="utf-8")

    skill = Skill(
        id=uuid4(),
        name=request.name,
        description=request.description,
        file_path=f".skills/{request.name}/SKILL.md",
        content_hash=hashlib.sha256(skill_content.encode("utf-8")).hexdigest(),
        status=SkillStatus.active.value ,
        version=1,
        source_run_id=None,
        created_at=now,
        updated_at=now,
        last_checked_at=now,
    )

    db.add(skill)
    db.commit()
    db.refresh(skill)

    return skill_to_dto(skill)
