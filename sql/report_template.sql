-- Live rolling 24-hour report, no secrets or personal payload.
SELECT * FROM auto01.report_24h;
SELECT state,count(*) FROM auto01.requests WHERE created_at>=now()-interval '24 hours' GROUP BY state;
SELECT request_id,state,deal_id,updated_at FROM auto01.requests WHERE state IN ('processing','crm_review','notification_failed') ORDER BY created_at;
-- Bind $1 as a parameter in the SQL client:
-- SELECT created_at,execution_id,event,severity,step,code,details FROM auto01.audit WHERE request_id=$1 ORDER BY id;
