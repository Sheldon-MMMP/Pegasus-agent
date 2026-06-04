CREATE TABLE IF NOT EXISTS settings (
  key varchar(100) PRIMARY KEY,
  value jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workspaces (
  id uuid PRIMARY KEY,
  name varchar(200) NOT NULL,
  root_path text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
  id uuid PRIMARY KEY,
  title varchar(300) NOT NULL,
  workspace_id uuid NOT NULL REFERENCES workspaces(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  last_message_at timestamptz
);

CREATE TABLE IF NOT EXISTS runs (
  id uuid PRIMARY KEY,
  session_id uuid NOT NULL REFERENCES sessions(id),
  status varchar(50) NOT NULL,
  approval_mode varchar(50) NOT NULL,
  model varchar(200) NOT NULL,
  error jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS messages (
  id uuid PRIMARY KEY,
  session_id uuid NOT NULL REFERENCES sessions(id),
  run_id uuid REFERENCES runs(id),
  role varchar(50) NOT NULL,
  content text NOT NULL,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS skills (
  id uuid PRIMARY KEY,
  name varchar(200) NOT NULL,
  description text NOT NULL,
  file_path text NOT NULL,
  content_hash varchar(128) NOT NULL,
  status varchar(50) NOT NULL,
  version integer NOT NULL DEFAULT 1,
  source_run_id uuid REFERENCES runs(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  last_checked_at timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS skills_name_unique ON skills(name);

CREATE TABLE IF NOT EXISTS tool_calls (
  id uuid PRIMARY KEY,
  run_id uuid NOT NULL REFERENCES runs(id),
  name varchar(200) NOT NULL,
  status varchar(50) NOT NULL,
  input jsonb NOT NULL,
  output jsonb,
  error jsonb,
  requires_approval boolean NOT NULL DEFAULT false,
  approval_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS approvals (
  id uuid PRIMARY KEY,
  run_id uuid NOT NULL REFERENCES runs(id),
  tool_call_id uuid NOT NULL REFERENCES tool_calls(id),
  status varchar(50) NOT NULL,
  reason text NOT NULL,
  requested_action jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz
);

CREATE TABLE IF NOT EXISTS memories (
  id uuid PRIMARY KEY,
  kind varchar(50) NOT NULL,
  content text NOT NULL,
  source_run_id uuid REFERENCES runs(id),
  source_message_id uuid REFERENCES messages(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
