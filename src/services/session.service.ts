import * as sessionRepository from "../repositories/session.repository.js";
import { ServiceError } from "../shared/service-error.js";

export async function listSessions(): Promise<{ sessions: Record<string, unknown>[] }> {
  return { sessions: await sessionRepository.listSessions() };
}

export async function getSession(sessionId: string): Promise<Record<string, unknown>> {
  const details = await sessionRepository.findSessionDetails(sessionId);
  if (!details.session) {
    throw new ServiceError("session_not_found", "Session not found.", 404);
  }
  return details as Record<string, unknown>;
}
