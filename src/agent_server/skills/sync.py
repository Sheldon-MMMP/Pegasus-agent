from datetime import UTC, datetime
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from agent_server.models import Skill
from agent_server.schemas import SkillStatus
from agent_server.skills.loader import discover_skill_files, parse_skill_file

def to_relative_skill_path(path: Path,project_root:Path) -> Path:
    return path.relative_to(project_root).as_posix()

def sync_skills(db: Session, skills_root: Path, project_root: Path) -> None:
    now = datetime.now(UTC)

    parsed_skills = [
        parse_skill_file(path)
        for path in discover_skill_files(skills_root)
    ]

    parsed_by_name = {
        skill.name: skill
        for skill in parsed_skills
    }

    existing_skills = db.scalars(select(Skill)).all()
    existing_by_name = {
        skill.name: skill
        for skill in existing_skills
    }

    for parsed in parsed_skills:
        existing = existing_by_name.get(parsed.name)
        relative_path = to_relative_skill_path(parsed.file_path, project_root)

        if existing is None:
            db.add(
                Skill(
                    name=parsed.name,
                    description=parsed.description,
                    file_path=relative_path,
                    content_hash=parsed.content_hash,
                    status=SkillStatus.active.value,
                    version=parsed.version,
                    source_run_id=None,
                    last_checked_at=now,
                )
            )
            continue

        existing.description = parsed.description
        existing.file_path = relative_path
        existing.content_hash = parsed.content_hash
        existing.version = parsed.version
        existing.last_checked_at = now

        if existing.status != SkillStatus.disabled.value:
            existing.status = SkillStatus.active.value

    for existing in existing_skills:
        if existing.name not in parsed_by_name:
            if existing.status != SkillStatus.disabled.value:
                existing.status = SkillStatus.missing.value
                existing.last_checked_at = now

    db.commit()
