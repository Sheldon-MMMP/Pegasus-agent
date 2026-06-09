import { ToolRegistry } from './tool-registry.js';
import { createMemoryListTool } from './tools/memory-list.tool.js';

export function createDefaultToolRegistry(): ToolRegistry {
    const registry = new ToolRegistry();

    registry.register(createMemoryListTool());

    return registry;
}
