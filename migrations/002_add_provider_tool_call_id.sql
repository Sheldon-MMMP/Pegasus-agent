ALTER TABLE tool_calls
  ADD COLUMN IF NOT EXISTS provider_tool_call_id text;

CREATE UNIQUE INDEX IF NOT EXISTS tool_calls_run_provider_tool_call_unique
  ON tool_calls(run_id, provider_tool_call_id)
  WHERE provider_tool_call_id IS NOT NULL;
