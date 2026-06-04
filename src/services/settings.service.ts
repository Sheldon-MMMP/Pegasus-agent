import type { SettingsValue, UpdateSettingsInput } from "../domain/types.js";
import * as settingsRepository from "../repositories/settings.repository.js";

function toDto(
  value: SettingsValue,
  workspace: Record<string, unknown>,
): Record<string, unknown> {
  const providerDto = (provider: SettingsValue["chat_provider"]) => ({
    base_url: provider.base_url,
    api_key_configured: Boolean(provider.api_key),
    model: provider.model,
  });
  return {
    approval_mode: value.approval_mode,
    chat_provider: providerDto(value.chat_provider),
    embedding_provider: providerDto(value.embedding_provider),
    milvus: value.milvus,
    workspace: {
      id: workspace.id,
      name: workspace.name,
      root_path: workspace.root_path,
    },
  };
}

export const getRawSettings = settingsRepository.getRawSettings;

export async function getSettings(): Promise<Record<string, unknown>> {
  const value = await settingsRepository.getRawSettings();
  const workspace = await settingsRepository.findWorkspace(value.default_workspace_id);
  return toDto(value, workspace);
}

export async function updateSettings(
  update: UpdateSettingsInput,
): Promise<Record<string, unknown>> {
  const { value, workspace } = await settingsRepository.applySettingsUpdate(update);
  return toDto(value, workspace);
}
