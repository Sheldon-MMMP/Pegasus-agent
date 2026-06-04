import type { Request, Response } from "express";
import { resolveApproval } from "../../../services/approval.service.js";
import { resolveApprovalSchema } from "../schemas/approval.schema.js";
import { uuidSchema } from "../schemas/common.schema.js";

export async function resolveToolApproval(
  request: Request,
  response: Response,
): Promise<void> {
  const approvalId = uuidSchema.parse(request.params.approvalId);
  const input = resolveApprovalSchema.parse(request.body);
  response.json(resolveApproval(approvalId, input.decision));
}
