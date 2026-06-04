import { Router } from "express";
import * as approvalController from "../controllers/approval.controller.js";
import * as chatController from "../controllers/chat.controller.js";
import * as memoryController from "../controllers/memory.controller.js";
import * as sessionController from "../controllers/session.controller.js";
import * as settingsController from "../controllers/settings.controller.js";
import * as skillController from "../controllers/skill.controller.js";
import { asyncHandler } from "../middleware/async-handler.js";

export function createApiRouter(): Router {
  const router = Router();

  router.get("/settings", asyncHandler(settingsController.getSettings));
  router.put("/settings", asyncHandler(settingsController.updateSettings));
  router.get("/sessions", asyncHandler(sessionController.listSessions));
  router.get("/sessions/:sessionId", asyncHandler(sessionController.getSession));
  router.post("/chat/runs", asyncHandler(chatController.createRun));
  router.get("/chat/runs/:runId/stream", asyncHandler(chatController.streamRun));
  router.get("/memories", asyncHandler(memoryController.listMemories));
  router.post("/memories", asyncHandler(memoryController.createMemory));
  router.get("/skills", asyncHandler(skillController.listSkills));
  router.get("/skills/:skillId", asyncHandler(skillController.getSkill));
  router.post("/skills", asyncHandler(skillController.createSkill));
  router.patch("/skills/:skillId", asyncHandler(skillController.updateSkill));
  router.post(
    "/tool-approvals/:approvalId",
    asyncHandler(approvalController.resolveToolApproval),
  );

  return router;
}
