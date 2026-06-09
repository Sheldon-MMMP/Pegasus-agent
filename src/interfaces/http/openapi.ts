import {
  extendZodWithOpenApi,
  OpenAPIRegistry,
  OpenApiGeneratorV3,
} from "@asteasolutions/zod-to-openapi";
import { z } from "zod";
import { resolveApprovalSchema } from "./schemas/approval.schema.js";
import { createRunSchema } from "./schemas/chat.schema.js";
import { uuidSchema } from "./schemas/common.schema.js";
import { createMemorySchema } from "./schemas/memory.schema.js";
import { updateSettingsSchema } from "./schemas/settings.schema.js";
import { createSkillSchema, updateSkillSchema } from "./schemas/skill.schema.js";

extendZodWithOpenApi(z);

const registry = new OpenAPIRegistry();

const jsonObjectSchema = z.object({}).passthrough();
const errorSchema = registry.register(
  "Error",
  z.object({
    detail: z.union([
      z.object({
        code: z.string(),
        message: z.string(),
        details: jsonObjectSchema.nullish(),
      }),
      jsonObjectSchema,
    ]),
  }),
);
const idParams = (name: string) => z.object({ [name]: uuidSchema });

const jsonResponse = (description: string, schema: z.ZodTypeAny = jsonObjectSchema) => ({
  description,
  content: { "application/json": { schema } },
});
const errorResponses = {
  422: jsonResponse("Request validation failed.", errorSchema),
  500: jsonResponse("Internal server error.", errorSchema),
};

registry.register("CreateRunInput", createRunSchema);
registry.register("ResolveApprovalInput", resolveApprovalSchema);
registry.register("CreateMemoryInput", createMemorySchema);
registry.register("UpdateSettingsInput", updateSettingsSchema);
registry.register("CreateSkillInput", createSkillSchema);
registry.register("UpdateSkillInput", updateSkillSchema);

registry.registerPath({
  method: "get",
  path: "/health",
  tags: ["System"],
  summary: "Check service health",
  responses: {
    200: jsonResponse("Service is healthy.", z.object({ status: z.literal("ok") })),
  },
});

registry.registerPath({
  method: "get",
  path: "/api/settings",
  tags: ["Settings"],
  summary: "Get settings",
  responses: { 200: jsonResponse("Current settings."), ...errorResponses },
});

registry.registerPath({
  method: "put",
  path: "/api/settings",
  tags: ["Settings"],
  summary: "Update settings",
  request: {
    body: { content: { "application/json": { schema: updateSettingsSchema } } },
  },
  responses: { 200: jsonResponse("Updated settings."), ...errorResponses },
});

registry.registerPath({
  method: "get",
  path: "/api/sessions",
  tags: ["Sessions"],
  summary: "List sessions",
  responses: { 200: jsonResponse("Sessions."), ...errorResponses },
});

registry.registerPath({
  method: "get",
  path: "/api/sessions/{sessionId}",
  tags: ["Sessions"],
  summary: "Get a session",
  request: { params: idParams("sessionId") },
  responses: {
    200: jsonResponse("Session details."),
    404: jsonResponse("Session not found.", errorSchema),
    ...errorResponses,
  },
});

registry.registerPath({
  method: "post",
  path: "/api/chat/runs",
  tags: ["Chat"],
  summary: "Create a chat run",
  request: {
    body: { content: { "application/json": { schema: createRunSchema } } },
  },
  responses: { 200: jsonResponse("Created chat run."), ...errorResponses },
});

registry.registerPath({
  method: "get",
  path: "/api/chat/runs/{run_id}/stream",
  tags: ["Chat"],
  summary: "Stream chat run events",
  description: "Returns server-sent events until the run reaches a terminal state.",
  request: { params: idParams("run_id") },
  responses: {
    200: {
      description: "Server-sent event stream.",
      content: {
        "text/event-stream": {
          schema: z.string().openapi({ example: 'data: {"type":"run.completed"}\n\n' }),
        },
      },
    },
    ...errorResponses,
  },
});

registry.registerPath({
  method: "get",
  path: "/api/memories",
  tags: ["Memories"],
  summary: "List memories",
  responses: { 200: jsonResponse("Memories."), ...errorResponses },
});

registry.registerPath({
  method: "post",
  path: "/api/memories",
  tags: ["Memories"],
  summary: "Create a memory",
  request: {
    body: { content: { "application/json": { schema: createMemorySchema } } },
  },
  responses: { 200: jsonResponse("Created memory."), ...errorResponses },
});

registry.registerPath({
  method: "get",
  path: "/api/skills",
  tags: ["Skills"],
  summary: "List skills",
  responses: { 200: jsonResponse("Skills."), ...errorResponses },
});

registry.registerPath({
  method: "get",
  path: "/api/skills/{skillId}",
  tags: ["Skills"],
  summary: "Get a skill",
  request: { params: idParams("skillId") },
  responses: {
    200: jsonResponse("Skill details."),
    404: jsonResponse("Skill not found.", errorSchema),
    ...errorResponses,
  },
});

registry.registerPath({
  method: "post",
  path: "/api/skills",
  tags: ["Skills"],
  summary: "Create a skill",
  request: {
    body: { content: { "application/json": { schema: createSkillSchema } } },
  },
  responses: {
    200: jsonResponse("Created skill."),
    409: jsonResponse("Skill already exists.", errorSchema),
    ...errorResponses,
  },
});

registry.registerPath({
  method: "patch",
  path: "/api/skills/{skillId}",
  tags: ["Skills"],
  summary: "Update a skill",
  request: {
    params: idParams("skillId"),
    body: { content: { "application/json": { schema: updateSkillSchema } } },
  },
  responses: {
    200: jsonResponse("Updated skill."),
    404: jsonResponse("Skill not found.", errorSchema),
    ...errorResponses,
  },
});

registry.registerPath({
  method: "post",
  path: "/api/tool-approvals/{approvalId}",
  tags: ["Approvals"],
  summary: "Resolve a tool approval",
  request: {
    params: idParams("approvalId"),
    body: { content: { "application/json": { schema: resolveApprovalSchema } } },
  },
  responses: {
    200: jsonResponse("Approval resolved."),
    404: jsonResponse("Approval not found.", errorSchema),
    ...errorResponses,
  },
});

export const openApiDocument = new OpenApiGeneratorV3(registry.definitions).generateDocument({
  openapi: "3.0.3",
  info: {
    title: "Agent Server API",
    version: "0.0.0",
    description: "HTTP API for the Agent Server.",
  },
  servers: [{ url: "/", description: "Current server" }],
  tags: [
    { name: "System" },
    { name: "Settings" },
    { name: "Sessions" },
    { name: "Chat" },
    { name: "Memories" },
    { name: "Skills" },
    { name: "Approvals" },
  ],
});
