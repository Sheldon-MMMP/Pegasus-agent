import { z } from "zod";

export const uuidSchema = z.string().uuid();
export const approvalModeSchema = z.enum(["sensitive", "auto"]);
