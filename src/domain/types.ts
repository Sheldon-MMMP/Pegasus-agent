export type JsonObject = Record<string, unknown>;
export type ApprovalMode = "sensitive" | "auto";
export type SkillStatus = "active" | "missing" | "disabled" | "error";
export type MemoryKind = "user_profile" | "agent_memory" | "project_fact";

export interface ErrorDto {
  code: string;
  message: string;
  details?: JsonObject | null;
}

export interface ChatProvider {
  base_url: string;
  api_key?: string | null;
  model: string;
}

export interface SettingsValue {
  approval_mode: ApprovalMode;
  chat_provider: ChatProvider;
  embedding_provider: ChatProvider;
  milvus: {
    uri: string;
    database?: string | null;
    status?: "unknown" | "connected" | "error" | null;
  };
  default_workspace_id: string;
}

export interface RunEvent {
  type: string;
  run_id: string;
  [key: string]: unknown;
}

export interface CreateRunInput {
  session_id?: string | null;
  workspace_id: string;
  message: string;
  approval_mode?: ApprovalMode | null;
  model?: string | null;
}

export interface CreateSkillInput {
  name: string;
  description: string;
  content: string;
}

export interface UpdateSkillInput {
  name?: string;
  description?: string;
  content?: string;
  status?: "active" | "disabled";
}

export interface UpdateSettingsInput {
  approval_mode?: ApprovalMode;
  chat_provider?: Partial<ChatProvider>;
  embedding_provider?: Partial<ChatProvider>;
  milvus?: { uri?: string; database?: string };
  workspace?: { name?: string; root_path?: string };
}
