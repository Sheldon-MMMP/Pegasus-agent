import type { AgentTool } from './tool.js';

export function toOpenAiTools(tools: AgentTool[]){
    return tools.map((tool)=>({
        type:"function" as const,
        function:{
            name:tool.name,
            description:tool.description,
            parameters:tool.parameters,
        }
    }))
}
