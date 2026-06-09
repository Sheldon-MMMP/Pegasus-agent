import type OpenAI from 'openai';
import type { ChatCompletionMessageParam } from 'openai/resources/chat/completions';
import type { ToolRegistry } from './tool-registry.js';
import { toOpenAiTools } from './openai-tools.js';

export interface RunAgentInput {
    client: OpenAI;
    model: string;
    messages: ChatCompletionMessageParam[];
    toolRegistry: ToolRegistry;
    onAssistantDelta(delta: string): void;

    onToolCallStarted?(event: {
        toolCallId: string;
        name: string;
        input: Record<string, unknown>;
    }): Promise<void> | void;

    onToolCallCompleted?(event: {
        toolCallId: string;
        name: string;
        output: unknown;
    }): Promise<void> | void;
    onToolCallFailed?(event: {
        toolCallId: string;
        name: string;
        error: unknown;
    }): Promise<void> | void;
}

export interface RunAgentResult {
    content: string;
    toolCalls: Array<{
        id?: string;
        name?: string;
        arguments: string;
    }>;
}

export async function runAgent(input: RunAgentInput): Promise<RunAgentResult> {
    const {
        toolRegistry,
        model,
        client,
        messages,
        onToolCallStarted,
        onToolCallCompleted,
        onToolCallFailed,
    } = input;
    const maxIterations = 5;
    const currentMessages = [...messages];
    const tools = toOpenAiTools(toolRegistry.list());

    for (let iteration = 0; iteration < maxIterations; iteration++) {
        // 当前这次 client.chat.completions.create 放这里
        const stream = await client.chat.completions.create({
            model,
            messages: currentMessages,
            tools,
            tool_choice: 'auto',
            stream: true,
        });

        const toolCallChunks = new Map<
            number,
            {
                id?: string;
                name?: string;
                arguments: string;
            }
        >();
        let content = '';
        for await (const chunk of stream) {
            const toolCalls = chunk.choices[0]?.delta.tool_calls;
            if (toolCalls) {
                for (const toolCall of toolCalls) {
                    const index = toolCall.index;
                    const existing = toolCallChunks.get(index) ?? {
                        arguments: '',
                    };

                    if (toolCall.id) existing.id = toolCall.id;
                    if (toolCall.function?.name) {
                        existing.name = toolCall.function.name;
                    }
                    if (toolCall.function?.arguments) {
                        existing.arguments += toolCall.function.arguments;
                    }
                    toolCallChunks.set(index, existing);
                }
            }
            const delta = chunk.choices[0]?.delta.content;

            if (!delta) continue;
            content += delta;
            input.onAssistantDelta(delta);
        }
        const toolCalls = [...toolCallChunks.values()];
        if (!toolCalls.length) {
            return { content, toolCalls };
        }
        const toolCallsList = toolCalls
            .filter((toolCall) => toolCall.id && toolCall.name)
            .map((toolCall) => ({
                id: toolCall.id!,
                type: 'function' as const,
                function: {
                    name: toolCall.name!,
                    arguments: toolCall.arguments || '{}',
                },
            }));

        currentMessages.push({
            role: 'assistant',
            content: content || null,
            tool_calls: toolCallsList,
        });
        for (const toolCall of toolCallsList) {
            const tool_name = toolCall.function.name ?? '';
            const tool = toolRegistry.get(tool_name);
            if (!tool) {
                await onToolCallFailed?.({
                    toolCallId: toolCall.id,
                    name: tool_name,
                    error: `Unknown tool: ${tool_name}`,
                });
                currentMessages.push({
                    role: 'tool',
                    tool_call_id: toolCall.id,
                    content: JSON.stringify({
                        error: `Unknown tool: ${tool_name}`,
                    }),
                });
                continue;
            }

            let toolInput: Record<string, unknown>;
            try {
                toolInput = toolCall.function.arguments
                    ? JSON.parse(toolCall.function.arguments)
                    : {};
            } catch {
                await onToolCallFailed?.({
                    toolCallId: toolCall.id,
                    name: tool.name,
                    error: 'Invalid tool arguments JSON.',
                });
                currentMessages.push({
                    role: 'tool',
                    tool_call_id: toolCall.id,
                    content: JSON.stringify({
                        error: 'Invalid tool arguments JSON.',
                    }),
                });
                continue;
            }
            await onToolCallStarted?.({
                toolCallId: toolCall.id,
                name: tool.name,
                input: toolInput,
            });
            let output: unknown;

            try {
                output = await tool.execute(toolInput);
            } catch (error) {
                await onToolCallFailed?.({
                    toolCallId: toolCall.id,
                    name: tool.name,
                    error,
                });
                currentMessages.push({
                    role: 'tool',
                    tool_call_id: toolCall.id,
                    content: JSON.stringify({
                        error:
                            error instanceof Error
                                ? error.message
                                : String(error),
                    }),
                });
                continue;
            }

            await onToolCallCompleted?.({
                toolCallId: toolCall.id,
                name: tool.name,
                output,
            });
            currentMessages.push({
                role: 'tool',
                tool_call_id: toolCall.id,
                content: JSON.stringify(output),
            });
        }
    }
    return {
        content: 'Agent stopped because it reached max iterations.',
        toolCalls: [],
    };
}
