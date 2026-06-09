import type { AgentTool } from '../tool.js';
import * as memoryRepository from '../../repositories/memory.repository.js';

export function createMemoryListTool(): AgentTool {
    return {
        name: 'memory_list',
        description: 'List saved memories that the agent can use as context.',
        parameters: {
            type: 'object',
            properties: {},
            additionalProperties: false,
        },
        async execute() {
            const memories = await memoryRepository.listMemories();
            return { memories };
        },
    };
}
