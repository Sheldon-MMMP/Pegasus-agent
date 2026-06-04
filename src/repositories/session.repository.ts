import { pool } from "../infrastructure/database.js";

export async function listSessions(): Promise<Record<string, unknown>[]> {
  return (await pool.query("SELECT * FROM sessions ORDER BY updated_at DESC")).rows;
}

export async function findSessionDetails(sessionId: string): Promise<{
  session: Record<string, unknown> | undefined;
  messages: Record<string, unknown>[];
  runs: Record<string, unknown>[];
}> {
  const [session, messages, runs] = await Promise.all([
    pool.query("SELECT * FROM sessions WHERE id = $1", [sessionId]),
    pool.query("SELECT * FROM messages WHERE session_id = $1 ORDER BY created_at", [
      sessionId,
    ]),
    pool.query("SELECT * FROM runs WHERE session_id = $1 ORDER BY created_at", [
      sessionId,
    ]),
  ]);
  return { session: session.rows[0], messages: messages.rows, runs: runs.rows };
}
