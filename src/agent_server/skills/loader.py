import hashlib


from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ParsedSkill:
    name: str
    description: str
    version: int
    content: str
    file_path: Path
    content_hash: str

def get_skills_root() -> Path:
    return Path.cwd() / ".skills"

def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_skill_file(path: Path) -> ParsedSkill:
    content = path.read_text(encoding="utf-8")
    metadata, _body = split_frontmatter(content)

    name = metadata.get("name")
    description = metadata.get("description")
    raw_version = metadata.get("version")

    if not name:
        raise ValueError("Skill frontmatter must include name.")

    if not description:
        raise ValueError("Skill frontmatter must include description.")

    if not raw_version:
        raise ValueError("Skill frontmatter must include version.")

    try:
        version = int(raw_version)
    except ValueError as exc:
        raise ValueError("Skill version must be an integer.") from exc

    return ParsedSkill(
        name=name,
        description=description,
        version=version,
        content=content,
        file_path=path,
        content_hash=compute_content_hash(content),
    )

def discover_skill_files(root: Path) -> list[Path]:
    if not root.exists():
        return []

    return sorted(root.glob("*/SKILL.md"))


def split_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---\n"):
        raise ValueError("Skill file must start with frontmatter.")

    end_marker = "\n---\n"
    end_index = content.find(end_marker, 4)

    if end_index == -1:
        raise ValueError("Skill frontmatter is not closed.")

    raw_frontmatter = content[4:end_index]
    body = content[end_index + len(end_marker):]

    metadata: dict[str, str] = {}

    for line in raw_frontmatter.splitlines():
        if not line.strip():
            continue

        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line}")

        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    return metadata, body