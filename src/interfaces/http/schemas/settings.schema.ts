import { z } from "zod";
import { approvalModeSchema } from "./common.schema.js";

export const updateSettingsSchema = z.object({
  approval_mode: approvalModeSchema.optional(),
  chat_provider: z.object({
    base_url: z.string().optional(),
    api_key: z.string().optional(),
    model: z.string().optional(),
  }).optional(),
  embedding_provider: z.object({
    base_url: z.string().optional(),
    api_key: z.string().optional(),
    model: z.string().optional(),
  }).optional(),
  milvus: z.object({
    uri: z.string().optional(),
    database: z.string().optional(),
  }).optional(),
  workspace: z.object({
    name: z.string().optional(),
    root_path: z.string().optional(),
  }).optional(),
});
