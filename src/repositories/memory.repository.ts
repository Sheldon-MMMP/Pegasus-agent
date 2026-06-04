import { randomUUID } from "node:crypto";
import type { MemoryKind } from "../domain/types.js";
import { pool } from "../infrastructure/database.js";

export async function listMemories(): Promise<Record<string, unknown>[]> {
  return (await pool.query("SELECT * FROM memories ORDER BY created_at DESC")).rows;
}

export async function createMemory(
  kind: MemoryKind,
  content: string,
): Promise<Record<string, unknown>> {
  const result = await pool.query(
    "INSERT INTO memories (id, kind, content) VALUES ($1, $2, $3) RETURNING *",
    [randomUUID(), kind, content],
  );
  return result.rows[0] as Record<string, unknown>;
}
