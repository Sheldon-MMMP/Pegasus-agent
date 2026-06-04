import { randomUUID } from "node:crypto";
import type { CreateRunInput, ErrorDto } from "../domain/types.js";
import { pool, withTransaction } from "../infrastructure/database.js";

export async function createQueuedRun(
  input: CreateRunInput,
  defaults: { approvalMode: string; model: string },
): Promise<{ run_id: string; session_id: string; status: string; stream_url: string }> {
  return withTransaction(async (client) => {
    const now = new Date();
    const sessionId = input.session_id ?? randomUUID();
    if (input.session_id) {
      const session = await client.query("SELECT * FROM sessions WHERE id = $1", [
        sessionId,
      ]);
      return createForExistingSession(client, session.rows[0], input, sessionId, now, defaults);
    }

    const workspace = await client.query("SELECT id FROM workspaces WHERE id = $1", [
      input.workspace_id,
    ]);
    if (!workspace.rows[0]) return Promise.reject(new Error("workspace_not_found"));
    await client.query(
      `INSERT INTO sessions (id, title, workspace_id, last_message_at)
       VALUES ($1, $2, $3, $4)`,
      [sessionId, input.message.slice(0, 80), input.workspace_id, now],
    );
    return insertRunAndMessage(client, input, sessionId, now, defaults);
  });
}

async function createForExistingSession(
  client: import("pg").PoolClient,
  session: Record<string, unknown> | undefined,
  input: CreateRunInput,
  sessionId: string,
  now: Date,
  defaults: { approvalMode: string; model: string },
) {
  if (!session) return Promise.reject(new Error("session_not_found"));
  if (session.workspace_id !== input.workspace_id) {
    return Promise.reject(new Error("workspace_mismatch"));
  }
  return insertRunAndMessage(client, input, sessionId, now, defaults);
}

async function insertRunAndMessage(
  client: import("pg").PoolClient,
  input: CreateRunInput,
  sessionId: string,
  now: Date,
  defaults: { approvalMode: string; model: string },
) {
  await client.query(
    "UPDATE sessions SET last_message_at = $1, updated_at = now() WHERE id = $2",
    [now, sessionId],
  );
  const runId = randomUUID();
  await client.query(
    `INSERT INTO runs (id, session_id, status, approval_mode, model)
     VALUES ($1, $2, 'queued', $3, $4)`,
    [runId, sessionId, input.approval_mode ?? defaults.approvalMode, input.model ?? defaults.model],
  );
  await client.query(
    `INSERT INTO messages (id, session_id, run_id, role, content)
     VALUES ($1, $2, $3, 'user', $4)`,
    [randomUUID(), sessionId, runId, input.message],
  );
  return {
    run_id: runId,
    session_id: sessionId,
    status: "queued",
    stream_url: `/api/chat/runs/${runId}/stream`,
  };
}

export async function startQueuedRun(runId: string) {
  return (
    await pool.query(
      `UPDATE runs SET status = 'running', started_at = now()
       WHERE id = $1 AND status = 'queued' RETURNING *`,
      [runId],
    )
  ).rows[0];
}

export async function findRun(runId: string) {
  return (await pool.query("SELECT * FROM runs WHERE id = $1", [runId])).rows[0];
}

export async function listChatMessages(sessionId: string) {
  return (
    await pool.query(
      "SELECT role, content FROM messages WHERE session_id = $1 ORDER BY created_at, id",
      [sessionId],
    )
  ).rows;
}

export async function saveAssistantMessage(
  messageId: string,
  sessionId: string,
  runId: string,
  content: string,
) {
  const inserted = await pool.query(
    `INSERT INTO messages (id, session_id, run_id, role, content)
     VALUES ($1, $2, $3, 'assistant', $4) RETURNING *`,
    [messageId, sessionId, runId, content],
  );
  await pool.query(
    "UPDATE sessions SET last_message_at = now(), updated_at = now() WHERE id = $1",
    [sessionId],
  );
  return inserted.rows[0];
}

export async function completeRun(runId: string) {
  return (
    await pool.query(
      "UPDATE runs SET status = 'completed', completed_at = now() WHERE id = $1 RETURNING completed_at",
      [runId],
    )
  ).rows[0];
}

export async function failRun(runId: string, error: ErrorDto): Promise<void> {
  await pool.query(
    "UPDATE runs SET status = 'failed', error = $2, completed_at = now() WHERE id = $1",
    [runId, error],
  );
}
