import { randomUUID } from "node:crypto";
import type { CreateRunInput, ErrorDto, RunEvent } from "../domain/types.js";
import { createOpenAiClient } from "../infrastructure/openai-client.js";
import { runEventBroker } from "../infrastructure/run-event-broker.js";
import * as chatRepository from "../repositories/chat.repository.js";
import { ServiceError } from "../shared/service-error.js";
import { getRawSettings } from "./settings.service.js";

export async function createRun(input: CreateRunInput) {
  const settings = await getRawSettings();
  try {
    return await chatRepository.createQueuedRun(input, {
      approvalMode: settings.approval_mode,
      model: settings.chat_provider.model,
    });
  } catch (error) {
    const code = error instanceof Error ? error.message : "";
    const mapping: Record<string, [string, number]> = {
      session_not_found: ["Session not found.", 404],
      workspace_not_found: ["Workspace not found.", 404],
      workspace_mismatch: ["Session workspace does not match request workspace.", 409],
    };
    const match = mapping[code];
    if (match) throw new ServiceError(code, match[0], match[1]);
    throw error;
  }
}

export async function executeRun(runId: string): Promise<void> {
  try {
    const run = await chatRepository.startQueuedRun(runId);
    if (!run) {
      const current = await chatRepository.findRun(runId);
      const error: ErrorDto = current
        ? { code: "run_already_started", message: `Run cannot start from status '${current.status}'.` }
        : { code: "run_not_found", message: "Run not found." };
      runEventBroker.publish(runId, { type: "run_failed", run_id: runId, error }, true);
      return;
    }

    runEventBroker.publish(runId, {
      type: "run_started",
      run_id: runId,
      session_id: run.session_id,
      created_at: run.started_at,
    });
    const settings = await getRawSettings();
    const client = createOpenAiClient(settings.chat_provider);
    const messages = await chatRepository.listChatMessages(run.session_id);
    const stream = await client.chat.completions.create({
      model: run.model,
      messages: messages.map((message) => ({
        role: message.role,
        content: message.content,
      })),
      stream: true,
    });

    const messageId = randomUUID();
    let content = "";
    for await (const chunk of stream) {
      const delta = chunk.choices[0]?.delta.content;
      if (!delta) continue;
      content += delta;
      runEventBroker.publish(runId, {
        type: "assistant_delta",
        run_id: runId,
        message_id: messageId,
        delta,
      });
    }
    const message = await chatRepository.saveAssistantMessage(
      messageId,
      run.session_id,
      runId,
      content,
    );
    runEventBroker.publish(runId, { type: "message_completed", run_id: runId, message });
    const completed = await chatRepository.completeRun(runId);
    runEventBroker.publish(
      runId,
      {
        type: "run_completed",
        run_id: runId,
        status: "completed",
        completed_at: completed.completed_at,
      },
      true,
    );
  } catch (cause) {
    const error: ErrorDto = {
      code: "run_execution_failed",
      message: "Run execution failed.",
      details: { reason: cause instanceof Error ? cause.message : String(cause) },
    };
    await chatRepository.failRun(runId, error);
    runEventBroker.publish(runId, { type: "run_failed", run_id: runId, error }, true);
  }
}

export async function getTerminalRunEvent(runId: string): Promise<RunEvent | null> {
  const run = await chatRepository.findRun(runId);
  if (!run) {
    return { type: "run_failed", run_id: runId, error: { code: "run_not_found", message: "Run not found." } };
  }
  if (run.status === "completed") {
    return { type: "run_completed", run_id: runId, status: "completed", completed_at: run.completed_at };
  }
  if (["failed", "cancelled"].includes(run.status)) {
    return {
      type: "run_failed",
      run_id: runId,
      error: run.error ?? { code: `run_${run.status}`, message: `Run ended with status '${run.status}'.` },
    };
  }
  return null;
}
