import type { JsonObject } from "../domain/types.js";

export class ServiceError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status = 500,
    public readonly details: JsonObject | null = null,
  ) {
    super(message);
  }
}
