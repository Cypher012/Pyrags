CREATE TABLE IF NOT EXISTS tutorial_retry_faults (
    job_id UUID PRIMARY KEY REFERENCES ingestion_jobs(id) ON DELETE CASCADE,
    fired BOOLEAN NOT NULL DEFAULT false
);

INSERT INTO tutorial_retry_faults (job_id)
SELECT id FROM ingestion_jobs
WHERE stage NOT IN ('completed', 'error')
ORDER BY created_at DESC
LIMIT 1
ON CONFLICT (job_id) DO UPDATE SET fired = false
RETURNING job_id;
