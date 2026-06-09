import type { AgentTool } from './tool.js';
import { ServiceError } from '../shared/service-error.js';

export class ToolRegistry {
  private readonly tools = new Map<string, AgentTool>();

  register(tool: AgentTool): void {
    // 将工具存入 tools
    const _tools = this.tools;
    if(_tools.has(tool.name)) throw new ServiceError('tool_already_exists', 'tool already exists');
    _tools.set(tool.name, tool);
  }

  get(name: string): AgentTool | undefined {
    // 根据名字查找工具
    return this.tools.get(name);
  }

  list(): AgentTool[]{
      return [...this.tools.values()];
  }
}
