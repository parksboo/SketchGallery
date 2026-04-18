CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY,
  title TEXT,
  prompt TEXT,
  style TEXT,
  sketch_name TEXT,
  sketch_path TEXT NOT NULL,
  result_path TEXT,
  status VARCHAR(32) NOT NULL,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at DESC);
