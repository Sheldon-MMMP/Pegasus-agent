import OpenAI from "openai";
import type { ChatProvider } from "../domain/types.js";
import { ServiceError } from "../shared/service-error.js";

export function createOpenAiClient(provider: ChatProvider): OpenAI {
  if (!provider.api_key) {
    throw new ServiceError(
      "chat_api_key_missing",
      "Chat provider API key is not configured.",
    );
  }
  return new OpenAI({ apiKey: provider.api_key, baseURL: provider.base_url });
}
