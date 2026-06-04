import { randomUUID } from "node:crypto";
import type pg from "pg";
import type { SettingsValue, UpdateSettingsInput } from "../domain/types.js";
import { pool, withTransaction } from "../infrastructure/database.js";

const APP_SETTINGS_KEY = "app";

function defaultSettings(workspaceId: string): SettingsValue {
  return {
    approval_mode: "sensitive",
    chat_provider: {
      base_url: "https://api.openai.com/v1",
      api_key: null,
      model: "gpt-4.1-mini",
    },
    embedding_provider: {
      base_url: "https://api.openai.com/v1",
      api_key: null,
      model: "text-embedding-3-small",
    },
    milvus: {
      uri: "http://localhost:19530",
      database: "default",
      status: "unknown",
    },
    default_workspace_id: workspaceId,
  };
}

async function ensureWorkspace(client: pg.PoolClient): Promise<Record<string, unknown>> {
  const existing = await client.query("SELECT * FROM workspaces LIMIT 1");
  if (existing.rows[0]) return existing.rows[0] as Record<string, unknown>;
  const created = await client.query(
    `INSERT INTO workspaces (id, name, root_path)
     VALUES ($1, 'Default Workspace', '.') RETURNING *`,
    [randomUUID()],
  );
  return created.rows[0] as Record<string, unknown>;
}

export async function getRawSettings(): Promise<SettingsValue> {
  return withTransaction(async (client) => {
    const workspace = await ensureWorkspace(client);
    const setting = await client.query("SELECT value FROM settings WHERE key = $1", [
      APP_SETTINGS_KEY,
    ]);
    if (!setting.rows[0]) {
      const value = defaultSettings(String(workspace.id));
      await client.query("INSERT INTO settings (key, value) VALUES ($1, $2)", [
        APP_SETTINGS_KEY,
        value,
      ]);
      return value;
    }

    const value = setting.rows[0].value as SettingsValue;
    const selected = await client.query("SELECT id FROM workspaces WHERE id = $1", [
      value.default_workspace_id,
    ]);
    if (!selected.rows[0]) {
      value.default_workspace_id = String(workspace.id);
      await client.query(
        "UPDATE settings SET value = $1, updated_at = now() WHERE key = $2",
        [value, APP_SETTINGS_KEY],
      );
    }
    return value;
  });
}

export async function findWorkspace(id: string): Promise<Record<string, unknown>> {
  const result = await pool.query("SELECT * FROM workspaces WHERE id = $1", [id]);
  return result.rows[0] as Record<string, unknown>;
}

export async function applySettingsUpdate(
  update: UpdateSettingsInput,
): Promise<{ value: SettingsValue; workspace: Record<string, unknown> }> {
  return withTransaction(async (client) => {
    const fallbackWorkspace = await ensureWorkspace(client);
    const setting = await client.query("SELECT value FROM settings WHERE key = $1", [
      APP_SETTINGS_KEY,
    ]);
    const value = (setting.rows[0]?.value ??
      defaultSettings(String(fallbackWorkspace.id))) as SettingsValue;

    if (update.approval_mode) value.approval_mode = update.approval_mode;
    if (update.chat_provider) Object.assign(value.chat_provider, update.chat_provider);
    if (update.embedding_provider) {
      Object.assign(value.embedding_provider, update.embedding_provider);
    }
    if (update.milvus) Object.assign(value.milvus, update.milvus);

    const selected = await client.query("SELECT * FROM workspaces WHERE id = $1", [
      value.default_workspace_id,
    ]);
    let workspace = (selected.rows[0] ?? fallbackWorkspace) as Record<string, unknown>;
    if (update.workspace) {
      const updated = await client.query(
        `UPDATE workspaces SET
          name = COALESCE($1, name),
          root_path = COALESCE($2, root_path),
          updated_at = now()
         WHERE id = $3 RETURNING *`,
        [update.workspace.name, update.workspace.root_path, value.default_workspace_id],
      );
      if (updated.rows[0]) workspace = updated.rows[0] as Record<string, unknown>;
    }

    await client.query(
      `INSERT INTO settings (key, value) VALUES ($1, $2)
       ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()`,
      [APP_SETTINGS_KEY, value],
    );
    return { value, workspace };
  });
}
