import hashlib
import re
from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, exists
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from agent_server.models import Skill
from agent_server.schemas import CreateSkillRequest, SkillStatus
from agent_server.services.exceptions import ServiceError

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def cleanup_created_file(path: Path) -> None:
    path.unlink(missing_ok=True)

    try:
        path.parent.rmdir()
    except OSError:
        pass

def validate_skill_name(name:str):
    if not SKILL_NAME_PATTERN.fullmatch(name):
        raise ServiceError(
            code="invalid_skill_name",
            message="Skill name must use lowercase letters, numbers, and hyphens.",
            details={"name": name},
        )

def build_skill_file_content(request: CreateSkillRequest) -> str:
    return (
        "---\n"
        f"name: {request.name}\n"
        f"description: {request.description}\n"
        "version: 1\n"
        "---\n\n"
        f"{request.content.rstrip()}\n"
    )


def create_skill(
    db: Session,
    request: CreateSkillRequest,
) -> Skill:

    validate_skill_name(request.name)

    is_exist = db.scalar(select(exists().where(Skill.name == request.name)))

    if is_exist:
        raise ServiceError(
            code="skill_already_exists",
            message="Skill already exists.",
            details={"name": request.name},
        )

    skill_file_path = Path.cwd() / ".skills" / request.name / "SKILL.md"

    if skill_file_path.exists():
        raise ServiceError(
            code="skill_file_already_exists",
            message="Skill file already exists.",
            details={"path": skill_file_path.as_posix()},
        )

    now = datetime.now(UTC)
    skill_content = build_skill_file_content(request)

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

    try:
        skill_file_path.parent.mkdir(parents=True, exist_ok=False)
        skill_file_path.write_text(skill_content, encoding="utf-8")
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        cleanup_created_file(skill_file_path)
        raise ServiceError(
            code="skill_already_exists",
            message="Skill already exists.",
            details={"name": request.name},
        ) from exc
    except FileExistsError as exc:
        db.rollback()
        raise ServiceError(
            code="skill_file_already_exists",
            message="Skill file already exists.",
            details={"path": skill_file_path.as_posix()},
        ) from exc
    except OSError as exc:
        db.rollback()
        cleanup_created_file(skill_file_path)
        raise ServiceError(
            code="skill_file_write_failed",
            message="Failed to write skill file.",
            details={"path": skill_file_path.as_posix()},
        ) from exc

    db.refresh(skill)

    return skill
