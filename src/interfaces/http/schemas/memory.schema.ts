import { z } from "zod";

export const createMemorySchema = z.object({
  kind: z.enum(["user_profile", "agent_memory", "project_fact"]),
  content: z.string().min(1),
});
