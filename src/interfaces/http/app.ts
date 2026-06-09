import express from "express";
import swaggerUi from "swagger-ui-express";
import { errorHandler } from "./middleware/error-handler.js";
import { openApiDocument } from "./openapi.js";
import { createApiRouter } from "./routes/index.js";

export function createApp(): express.Express {
  const app = express();
  app.use(express.json());
  app.get("/openapi.json", (_request, response) => response.json(openApiDocument));
  app.use("/docs", swaggerUi.serve, swaggerUi.setup(openApiDocument));
  app.get("/health", (_request, response) => response.json({ status: "ok" }));
  app.use("/api", createApiRouter());
  app.use(errorHandler);
  return app;
}
