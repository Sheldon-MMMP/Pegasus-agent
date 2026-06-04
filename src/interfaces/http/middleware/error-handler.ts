import type { NextFunction, Request, Response } from "express";
import { ZodError } from "zod";
import { ServiceError } from "../../../shared/service-error.js";

export function errorHandler(
  error: unknown,
  _request: Request,
  response: Response,
  _next: NextFunction,
): void {
  if (error instanceof ServiceError) {
    response.status(error.status).json({
      detail: {
        code: error.code,
        message: error.message,
        details: error.details,
      },
    });
    return;
  }
  if (error instanceof ZodError) {
    response.status(422).json({ detail: error.flatten() });
    return;
  }
  console.error(error);
  response.status(500).json({
    detail: { code: "internal_error", message: "Internal server error." },
  });
}
