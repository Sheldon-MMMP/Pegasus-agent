import hashlib
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, exists
from sqlalchemy.orm import Session

from agent_server.db import get_db
from agent_server.models import Skill
from agent_server.schemas import (
    CreateSkillRequest,
    GetSkillResponse,
    ListSkillsResponse,
    SkillDTO,
    SkillStatus,
    UpdateSkillRequest,
)
from agent_server.skills.loader import split_frontmatter
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


def build_skill_content(name: str, description: str, content: str) -> str:
    content = content.strip("\n")

    return f"""---
name: {name}
description: {description}
version: 1
---

{content}
"""

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


    skill_content = build_skill_content(
        name=request.name,
        description=request.description,
        content=request.content,
    )

    if skill_file_path.parent.exists():
        raise HTTPException(
            status_code=409,
            detail="Skill path already exists.",
        )

    skill_file_path.parent.mkdir(parents=True, exist_ok=False)
    skill_file_path.write_text(skill_content, encoding="utf-8")

    skill = Skill(
        id=uuid4(),
        name=request.name,
        description=request.description,
        file_path=f".skills/{request.name}/SKILL.md",
        content_hash=hashlib.sha256(skill_content.encode("utf-8")).hexdigest(),
        status=SkillStatus.active.value,
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


@router.patch("/{skill_id}", response_model=SkillDTO)
def update_skill(skill_id: UUID, request: UpdateSkillRequest, db: DbSession) -> SkillDTO:
    if not request.model_fields_set:
        raise HTTPException(status_code=400, detail="No skill updates provided.")

    if all(
        value is None
        for value in (request.name, request.description, request.content, request.status)
    ):
        raise HTTPException(status_code=400, detail="No skill updates provided.")

    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found.")

    if skill.status in {SkillStatus.missing.value, SkillStatus.error.value}:
        raise HTTPException(
            status_code=409,
            detail="Cannot update a missing or invalid skill.",
        )

    current_path = resolve_skill_path(skill.file_path)
    if not current_path.exists():
        if skill.status != SkillStatus.disabled.value:
            skill.status = SkillStatus.missing.value
            skill.last_checked_at = datetime.now(UTC)
            db.commit()

        raise HTTPException(status_code=409, detail="Skill file is missing.")

    try:
        current_content = current_path.read_text(encoding="utf-8")
        _metadata, current_body = split_frontmatter(current_content)
        if current_body.startswith("\n"):
            current_body = current_body[1:]
    except ValueError as exc:
        skill.status = SkillStatus.error.value
        skill.last_checked_at = datetime.now(UTC)
        db.commit()
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    new_name = request.name if request.name is not None else skill.name
    new_description = (
        request.description if request.description is not None else skill.description
    )
    new_body = request.content if request.content is not None else current_body
    new_status = request.status if request.status is not None else skill.status

    if new_name != skill.name:
        name_exists = db.scalar(
            select(exists().where(Skill.name == new_name, Skill.id != skill.id))
        )
        if name_exists:
            raise HTTPException(status_code=409, detail="Skill name already exists.")

    new_path = Path.cwd() / ".skills" / new_name / "SKILL.md"
    if new_name != skill.name and new_path.parent.exists():
        raise HTTPException(status_code=409, detail="Skill path already exists.")

    new_content = build_skill_content(
        name=new_name,
        description=new_description,
        content=new_body,
    )

    target_path = current_path
    if new_name != skill.name:
        current_path.parent.rename(new_path.parent)
        target_path = new_path

    target_path.write_text(new_content, encoding="utf-8")

    now = datetime.now(UTC)
    skill.name = new_name
    skill.description = new_description
    skill.file_path = f".skills/{new_name}/SKILL.md"
    skill.content_hash = hashlib.sha256(new_content.encode("utf-8")).hexdigest()
    skill.status = new_status
    skill.last_checked_at = now

    db.commit()
    db.refresh(skill)

    return skill_to_dto(skill)
