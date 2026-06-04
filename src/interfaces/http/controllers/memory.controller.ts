import type { Request, Response } from "express";
import * as memoryService from "../../../services/memory.service.js";
import { createMemorySchema } from "../schemas/memory.schema.js";

export async function listMemories(_request: Request, response: Response): Promise<void> {
  response.json(await memoryService.listMemories());
}

export async function createMemory(request: Request, response: Response): Promise<void> {
  const input = createMemorySchema.parse(request.body);
  response.json(await memoryService.createMemory(input.kind, input.content));
}
