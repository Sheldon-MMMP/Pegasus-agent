import { randomUUID } from "node:crypto";
import type { SkillStatus } from "../domain/types.js";
import { pool, withTransaction } from "../infrastructure/database.js";

export interface SkillRecord {
  id: string;
  name: string;
  description: string;
  file_path: string;
  content_hash: string;
  status: SkillStatus;
  version: number;
  [key: string]: unknown;
}

export interface ParsedSkillRecord {
  name: string;
  description: string;
  version: number;
  file_path: string;
  content_hash: string;
}

export async function synchronizeSkills(skills: ParsedSkillRecord[]): Promise<void> {
  await withTransaction(async (client) => {
    const names = skills.map((skill) => skill.name);
    for (const skill of skills) {
      await client.query(
        `INSERT INTO skills
          (id, name, description, file_path, content_hash, status, version, last_checked_at)
         VALUES ($1, $2, $3, $4, $5, 'active', $6, now())
         ON CONFLICT (name) DO UPDATE SET
          description = EXCLUDED.description,
          file_path = EXCLUDED.file_path,
          content_hash = EXCLUDED.content_hash,
          version = EXCLUDED.version,
          status = CASE WHEN skills.status = 'disabled' THEN 'disabled' ELSE 'active' END,
          last_checked_at = now(), updated_at = now()`,
        [randomUUID(), skill.name, skill.description, skill.file_path, skill.content_hash, skill.version],
      );
    }
    await client.query(
      `UPDATE skills SET status = 'missing', last_checked_at = now(), updated_at = now()
       WHERE status <> 'disabled' AND NOT (name = ANY($1::text[]))`,
      [names],
    );
  });
}

export async function listSkills(): Promise<SkillRecord[]> {
  return (await pool.query("SELECT * FROM skills ORDER BY updated_at DESC")).rows;
}

export async function findSkill(id: string): Promise<SkillRecord | undefined> {
  return (await pool.query("SELECT * FROM skills WHERE id = $1", [id])).rows[0];
}

export async function markMissing(id: string): Promise<void> {
  await pool.query(
    "UPDATE skills SET status = 'missing', last_checked_at = now() WHERE id = $1",
    [id],
  );
}

export async function insertSkill(skill: ParsedSkillRecord): Promise<SkillRecord> {
  const result = await pool.query(
    `INSERT INTO skills
      (id, name, description, file_path, content_hash, status, version, last_checked_at)
     VALUES ($1, $2, $3, $4, $5, 'active', $6, now()) RETURNING *`,
    [randomUUID(), skill.name, skill.description, skill.file_path, skill.content_hash, skill.version],
  );
  return result.rows[0];
}

export async function updateSkill(
  id: string,
  skill: ParsedSkillRecord & { status: SkillStatus },
): Promise<SkillRecord> {
  const result = await pool.query(
    `UPDATE skills SET name = $1, description = $2, file_path = $3,
      content_hash = $4, status = $5, version = $6,
      last_checked_at = now(), updated_at = now()
     WHERE id = $7 RETURNING *`,
    [skill.name, skill.description, skill.file_path, skill.content_hash, skill.status, skill.version, id],
  );
  return result.rows[0];
}
