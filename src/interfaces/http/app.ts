import express from "express";
import swaggerUi from "swagger-ui-express";
import { errorHandler } from "./middleware/error-handler.js";
import { openApiDocument } from "./openapi.js";
import { createApiRouter } from "./routes/index.js";

const allowedOrigins = new Set([
  "http://localhost:3000",
  "http://127.0.0.1:3000",
]);

function applyCors(
  request: express.Request,
  response: express.Response,
  next: express.NextFunction,
): void {
  const origin = request.headers.origin;

  if (origin && allowedOrigins.has(origin)) {
    response.setHeader("Access-Control-Allow-Origin", origin);
    response.setHeader("Vary", "Origin");
    response.setHeader(
      "Access-Control-Allow-Methods",
      "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    );
    response.setHeader(
      "Access-Control-Allow-Headers",
      "Content-Type, Authorization",
    );
  }

  if (request.method === "OPTIONS") {
    response.status(204).end();
    return;
  }

  next();
}

export function createApp(): express.Express {
  const app = express();
  app.use(applyCors);
  app.use(express.json());
  app.get("/openapi.json", (_request, response) => response.json(openApiDocument));
  app.use("/docs", swaggerUi.serve, swaggerUi.setup(openApiDocument));
  app.get("/health", (_request, response) => response.json({ status: "ok" }));
  app.use("/api", createApiRouter());
  app.use(errorHandler);
  return app;
}
