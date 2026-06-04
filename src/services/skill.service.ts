import { createHash } from "node:crypto";
import { mkdir, readFile, readdir, rename, rm, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import type { CreateSkillInput, UpdateSkillInput } from "../domain/types.js";
import * as skillRepository from "../repositories/skill.repository.js";
import { ServiceError } from "../shared/service-error.js";

const SKILLS_ROOT = path.join(process.cwd(), ".skills");
const NAME_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

function hash(content: string): string {
  return createHash("sha256").update(content).digest("hex");
}

function splitFrontmatter(content: string): {
  metadata: Record<string, string>;
  body: string;
} {
  if (!content.startsWith("---\n")) throw new Error("Skill file must start with frontmatter.");
  const end = content.indexOf("\n---\n", 4);
  if (end === -1) throw new Error("Skill frontmatter is not closed.");
  const metadata: Record<string, string> = {};
  for (const line of content.slice(4, end).split("\n")) {
    if (!line.trim()) continue;
    const index = line.indexOf(":");
    if (index === -1) throw new Error(`Invalid frontmatter line: ${line}`);
    metadata[line.slice(0, index).trim()] = line.slice(index + 1).trim();
  }
  return { metadata, body: content.slice(end + 5) };
}

function buildContent(name: string, description: string, body: string): string {
  return `---\nname: ${name}\ndescription: ${description}\nversion: 1\n---\n\n${body.replace(/\n+$/, "")}\n`;
}

async function exists(filePath: string): Promise<boolean> {
  try {
    await stat(filePath);
    return true;
  } catch {
    return false;
  }
}

export async function syncSkills(): Promise<void> {
  await mkdir(SKILLS_ROOT, { recursive: true });
  const entries = await readdir(SKILLS_ROOT, { withFileTypes: true });
  const parsed: skillRepository.ParsedSkillRecord[] = [];
  for (const entry of entries.filter((item) => item.isDirectory())) {
    const filePath = path.join(SKILLS_ROOT, entry.name, "SKILL.md");
    if (!(await exists(filePath))) continue;
    try {
      const content = await readFile(filePath, "utf8");
      const { metadata } = splitFrontmatter(content);
      if (!metadata.name || !metadata.description || !metadata.version) continue;
      parsed.push({
        name: metadata.name,
        description: metadata.description,
        version: Number(metadata.version),
        file_path: path.relative(process.cwd(), filePath),
        content_hash: hash(content),
      });
    } catch (error) {
      console.warn(`Could not parse ${filePath}:`, error);
    }
  }
  await skillRepository.synchronizeSkills(parsed);
}

export async function listSkills() {
  return { skills: await skillRepository.listSkills() };
}

export async function getSkill(id: string) {
  const skill = await skillRepository.findSkill(id);
  if (!skill) throw new ServiceError("skill_not_found", "Skill not found.", 404);
  const filePath = path.resolve(skill.file_path);
  if (!(await exists(filePath))) {
    if (skill.status !== "disabled") {
      await skillRepository.markMissing(id);
      skill.status = "missing";
    }
    return { skill, content: null };
  }
  return { skill, content: await readFile(filePath, "utf8") };
}

export async function createSkill(input: CreateSkillInput) {
  if (!NAME_PATTERN.test(input.name)) {
    throw new ServiceError("invalid_skill_name", "Skill name must use lowercase letters, numbers, and hyphens.", 422);
  }
  const directory = path.join(SKILLS_ROOT, input.name);
  if (await exists(directory)) {
    throw new ServiceError("skill_file_already_exists", "Skill path already exists.", 409);
  }
  const content = buildContent(input.name, input.description, input.content);
  await mkdir(directory);
  await writeFile(path.join(directory, "SKILL.md"), content, "utf8");
  try {
    return await skillRepository.insertSkill({
      name: input.name,
      description: input.description,
      file_path: `.skills/${input.name}/SKILL.md`,
      content_hash: hash(content),
      version: 1,
    });
  } catch {
    await rm(directory, { recursive: true, force: true });
    throw new ServiceError("skill_already_exists", "Skill already exists.", 409);
  }
}

export async function updateSkill(id: string, input: UpdateSkillInput) {
  if (Object.keys(input).length === 0) {
    throw new ServiceError("no_skill_updates", "No skill updates provided.", 400);
  }
  const skill = await skillRepository.findSkill(id);
  if (!skill) throw new ServiceError("skill_not_found", "Skill not found.", 404);
  if (["missing", "error"].includes(skill.status)) {
    throw new ServiceError("skill_not_editable", "Cannot update a missing or invalid skill.", 409);
  }
  const currentPath = path.resolve(skill.file_path);
  if (!(await exists(currentPath))) {
    throw new ServiceError("skill_file_missing", "Skill file is missing.", 409);
  }
  const current = splitFrontmatter(await readFile(currentPath, "utf8"));
  const name = input.name ?? skill.name;
  const description = input.description ?? skill.description;
  const content = buildContent(name, description, input.content ?? current.body);
  let targetPath = currentPath;
  if (name !== skill.name) {
    const targetDirectory = path.join(SKILLS_ROOT, name);
    if (await exists(targetDirectory)) {
      throw new ServiceError("skill_file_already_exists", "Skill path already exists.", 409);
    }
    await rename(path.dirname(currentPath), targetDirectory);
    targetPath = path.join(targetDirectory, "SKILL.md");
  }
  await writeFile(targetPath, content, "utf8");
  return skillRepository.updateSkill(id, {
    name,
    description,
    file_path: `.skills/${name}/SKILL.md`,
    content_hash: hash(content),
    version: 1,
    status: input.status ?? skill.status,
  });
}
