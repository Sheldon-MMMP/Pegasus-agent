import { z } from "zod";

export const createSkillSchema = z.object({
  name: z.string().min(1).max(80).regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/),
  description: z.string().min(1),
  content: z.string(),
});

export const updateSkillSchema = createSkillSchema.partial().extend({
  status: z.enum(["active", "disabled"]).optional(),
});
