CREATE SCHEMA IF NOT EXISTS auto01;
CREATE TABLE IF NOT EXISTS auto01.requests (
 request_id text PRIMARY KEY,
 payload jsonb NOT NULL,
 state text NOT NULL DEFAULT 'processing',
 deal_id bigint,
 error text,
 notified boolean NOT NULL DEFAULT false,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS auto01.events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 request_id text NOT NULL REFERENCES auto01.requests,
 event text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
