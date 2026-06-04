import type { Request, Response } from "express";
import * as sessionService from "../../../services/session.service.js";
import { uuidSchema } from "../schemas/common.schema.js";

export async function listSessions(_request: Request, response: Response): Promise<void> {
  response.json(await sessionService.listSessions());
}

export async function getSession(request: Request, response: Response): Promise<void> {
  response.json(await sessionService.getSession(uuidSchema.parse(request.params.sessionId)));
}
