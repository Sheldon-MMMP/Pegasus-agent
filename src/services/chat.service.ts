import { randomUUID } from 'node:crypto';
import type { CreateRunInput, ErrorDto, RunEvent } from '../domain/types.js';
import { createOpenAiClient } from '../infrastructure/openai-client.js';
import { runEventBroker } from '../infrastructure/run-event-broker.js';
import * as chatRepository from '../repositories/chat.repository.js';
import { ServiceError } from '../shared/service-error.js';
import { getRawSettings } from './settings.service.js';
import { createDefaultToolRegistry } from '../runtime/default-tool-registry.js';
import { runAgent } from '../runtime/agent-runtime.js';

export async function createRun(input: CreateRunInput) {
    const settings = await getRawSettings();
    try {
        return await chatRepository.createQueuedRun(input, {
            approvalMode: settings.approval_mode,
            model: settings.chat_provider.model,
        });
    } catch (error) {
        const code = error instanceof Error ? error.message : '';
        const mapping: Record<string, [string, number]> = {
            session_not_found: ['Session not found.', 404],
            workspace_not_found: ['Workspace not found.', 404],
            workspace_mismatch: [
                'Session workspace does not match request workspace.',
                409,
            ],
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
                ? {
                      code: 'run_already_started',
                      message: `Run cannot start from status '${current.status}'.`,
                  }
                : { code: 'run_not_found', message: 'Run not found.' };
            runEventBroker.publish(
                runId,
                { type: 'run_failed', run_id: runId, error },
                true,
            );
            return;
        }

        runEventBroker.publish(runId, {
            type: 'run_started',
            run_id: runId,
            session_id: run.session_id,
            created_at: run.started_at,
        });

        const settings = await getRawSettings();
        const client = createOpenAiClient(settings.chat_provider);
        const toolRegistry = createDefaultToolRegistry();
        const messages = await chatRepository.listChatMessages(run.session_id);

        const openAiMessages = messages.map((message) => ({
            role: message.role,
            content: message.content,
        }));

        const messageId = randomUUID();

        const result = await runAgent({
            client,
            model: run.model,
            messages: openAiMessages,
            toolRegistry,
            onAssistantDelta(delta) {
                runEventBroker.publish(runId, {
                    type: 'assistant_delta',
                    run_id: runId,
                    message_id: messageId,
                    delta,
                });
            },
            async onToolCallStarted(event: {
                toolCallId: string;
                name: string;
                input: Record<string, unknown>;
            }) {
                await chatRepository.createToolCallStarted({
                    runId,
                    providerToolCallId: event.toolCallId,
                    name: event.name,
                    input: event.input,
                });
                runEventBroker.publish(runId, {
                    type: 'tool_call_started',
                    run_id: runId,
                    tool_call_id: event.toolCallId,
                    name: event.name,
                    input: event.input,
                });
            },

            async onToolCallCompleted(event: {
                toolCallId: string;
                name: string;
                output: unknown;
            }) {
                await chatRepository.completeToolCall({
                    runId,
                    providerToolCallId: event.toolCallId,
                    output: event.output,
                });
                runEventBroker.publish(runId, {
                    type: 'tool_call_completed',
                    run_id: runId,
                    tool_call_id: event.toolCallId,
                    name: event.name,
                    output: event.output,
                });
            },
            async onToolCallFailed(event: {
                toolCallId: string;
                name: string;
                error: unknown;
            }) {
                await chatRepository.failToolCall({
                    runId,
                    providerToolCallId: event.toolCallId,
                    name: event.name,
                    error:
                        event.error instanceof Error
                            ? { message: event.error.message }
                            : event.error,
                });
                runEventBroker.publish(runId, {
                    type: 'tool_call_failed',
                    run_id: runId,
                    tool_call_id: event.toolCallId,
                    name: event.name,
                    error:
                        event.error instanceof Error
                            ? { message: event.error.message }
                            : event.error,
                });
            },
        });

        const content = result.content;

        const message = await chatRepository.saveAssistantMessage(
            messageId,
            run.session_id,
            runId,
            content,
        );
        runEventBroker.publish(runId, {
            type: 'message_completed',
            run_id: runId,
            message,
        });
        const completed = await chatRepository.completeRun(runId);
        runEventBroker.publish(
            runId,
            {
                type: 'run_completed',
                run_id: runId,
                status: 'completed',
                completed_at: completed.completed_at,
            },
            true,
        );
    } catch (cause) {
        const error: ErrorDto = {
            code: 'run_execution_failed',
            message: 'Run execution failed.',
            details: {
                reason: cause instanceof Error ? cause.message : String(cause),
            },
        };
        await chatRepository.failRun(runId, error);
        runEventBroker.publish(
            runId,
            { type: 'run_failed', run_id: runId, error },
            true,
        );
    }
}

export async function getTerminalRunEvent(
    runId: string,
): Promise<RunEvent | null> {
    const run = await chatRepository.findRun(runId);
    if (!run) {
        return {
            type: 'run_failed',
            run_id: runId,
            error: { code: 'run_not_found', message: 'Run not found.' },
        };
    }
    if (run.status === 'completed') {
        return {
            type: 'run_completed',
            run_id: runId,
            status: 'completed',
            completed_at: run.completed_at,
        };
    }
    if (['failed', 'cancelled'].includes(run.status)) {
        return {
            type: 'run_failed',
            run_id: runId,
            error: run.error ?? {
                code: `run_${run.status}`,
                message: `Run ended with status '${run.status}'.`,
            },
        };
    }
    return null;
}
