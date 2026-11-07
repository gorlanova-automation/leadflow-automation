CREATE TABLE IF NOT EXISTS auto01.audit (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 created_at timestamptz NOT NULL DEFAULT now(),
 execution_id text NOT NULL,
 request_id text,
 event text NOT NULL,
 severity text NOT NULL CHECK(severity IN ('INFO','WARN','ERROR')),
 step text NOT NULL,
 code text NOT NULL,
 details jsonb NOT NULL DEFAULT '{}'::jsonb
);
ALTER TABLE auto01.audit OWNER TO auto01;
CREATE INDEX IF NOT EXISTS audit_execution_idx ON auto01.audit(execution_id);
CREATE INDEX IF NOT EXISTS audit_request_idx ON auto01.audit(request_id);
CREATE OR REPLACE VIEW auto01.report_24h AS
SELECT now() AS generated_at,
count(*)::int AS total,
count(*) FILTER (WHERE deal_id IS NOT NULL)::int AS created,
count(*) FILTER (WHERE state='complete')::int AS complete,
count(*) FILTER (WHERE state='crm_review')::int AS crm_review,
count(*) FILTER (WHERE state='notification_failed')::int AS notification_failed
FROM auto01.requests WHERE created_at>=now()-interval '24 hours';
ALTER VIEW auto01.report_24h OWNER TO auto01;
