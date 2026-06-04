import type { NextFunction, Request, Response } from "express";

export function asyncHandler(
  handler: (request: Request, response: Response) => Promise<unknown>,
) {
  return (request: Request, response: Response, next: NextFunction): void => {
    void handler(request, response).catch(next);
  };
}
