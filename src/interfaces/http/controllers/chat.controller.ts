import type { Request, Response } from "express";
import { runEventBroker } from "../../../infrastructure/run-event-broker.js";
import * as chatService from "../../../services/chat.service.js";
import { createRunSchema } from "../schemas/chat.schema.js";
import { uuidSchema } from "../schemas/common.schema.js";

function writeSse(response: Response, event: unknown): void {
  response.write(`data: ${JSON.stringify(event)}\n\n`);
}

export async function createRun(request: Request, response: Response): Promise<void> {
  const run = await chatService.createRun(createRunSchema.parse(request.body));
  response.json(run);
  setImmediate(() => void chatService.executeRun(run.run_id));
}

export async function streamRun(request: Request, response: Response): Promise<void> {
  const runId = uuidSchema.parse(request.params.runId);
  response.setHeader("Content-Type", "text/event-stream");
  response.setHeader("Cache-Control", "no-cache");
  response.setHeader("Connection", "keep-alive");
  response.flushHeaders();

  const terminal = await chatService.getTerminalRunEvent(runId);
  if (terminal) {
    writeSse(response, terminal);
    response.end();
    return;
  }
  for await (const event of runEventBroker.subscribe(runId)) writeSse(response, event);
  response.end();
}
