import { z } from "zod";
import { approvalModeSchema, uuidSchema } from "./common.schema.js";

export const createRunSchema = z.object({
  session_id: uuidSchema.nullish(),
  workspace_id: uuidSchema,
  message: z.string().min(1),
  approval_mode: approvalModeSchema.nullish(),
  model: z.string().min(1).nullish(),
});
