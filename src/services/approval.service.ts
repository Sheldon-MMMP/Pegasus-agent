import { randomUUID } from "node:crypto";

export function resolveApproval(approvalId: string, decision: "approved" | "rejected") {
  const now = new Date();
  const runId = randomUUID();
  const toolCallId = randomUUID();
  const approved = decision === "approved";
  const action = {
    tool_name: "file_write",
    input: { path: "README.md", content: "Add a short project summary." },
  };

  return {
    approval: {
      id: approvalId,
      run_id: runId,
      tool_call_id: toolCallId,
      status: approved ? "approved" : "rejected",
      reason: "file_write 会修改 workspace 内的文件，需要用户确认。",
      requested_action: action,
      created_at: now,
      resolved_at: now,
    },
    tool_call: {
      id: toolCallId,
      run_id: runId,
      name: "file_write",
      status: approved ? "succeeded" : "rejected",
      input: action.input,
      output: approved ? { path: "README.md", bytes_written: 28 } : null,
      error: null,
      requires_approval: true,
      approval_id: approvalId,
      created_at: now,
      started_at: approved ? now : null,
      completed_at: now,
    },
    run: {
      id: runId,
      session_id: randomUUID(),
      status: "completed",
      approval_mode: "sensitive",
      model: "gpt-4.1-mini",
      error: null,
      created_at: now,
      started_at: now,
      completed_at: now,
    },
  };
}
