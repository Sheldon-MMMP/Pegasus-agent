import express from "express";
import { errorHandler } from "./middleware/error-handler.js";
import { createApiRouter } from "./routes/index.js";

export function createApp(): express.Express {
  const app = express();
  app.use(express.json());
  app.get("/health", (_request, response) => response.json({ status: "ok" }));
  app.use("/api", createApiRouter());
  app.use(errorHandler);
  return app;
}
