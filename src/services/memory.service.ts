import type { MemoryKind } from "../domain/types.js";
import * as memoryRepository from "../repositories/memory.repository.js";

export async function listMemories(): Promise<{ memories: Record<string, unknown>[] }> {
  return { memories: await memoryRepository.listMemories() };
}

export async function createMemory(
  kind: MemoryKind,
  content: string,
): Promise<Record<string, unknown>> {
  return memoryRepository.createMemory(kind, content);
}
