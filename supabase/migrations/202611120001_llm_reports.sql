BEGIN;

CREATE SCHEMA IF NOT EXISTS llm_reports;
REVOKE ALL ON SCHEMA llm_reports FROM PUBLIC;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reports_runtime') THEN
        CREATE ROLE reports_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS llm_reports.source_state (
    source_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL CHECK (jsonb_typeof(payload::jsonb) = 'object')
);

CREATE TABLE IF NOT EXISTS llm_reports.releases (
    release_key TEXT PRIMARY KEY,
    payload TEXT NOT NULL CHECK (jsonb_typeof(payload::jsonb) = 'object')
);

CREATE TABLE IF NOT EXISTS llm_reports.report_versions (
    report_id TEXT NOT NULL,
    revision TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (jsonb_typeof(payload::jsonb) = 'object'),
    PRIMARY KEY (report_id, revision)
);

REVOKE ALL ON ALL TABLES IN SCHEMA llm_reports FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA llm_reports TO reports_runtime;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA llm_reports TO reports_runtime;

ALTER TABLE llm_reports.source_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_reports.releases ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_reports.report_versions ENABLE ROW LEVEL SECURITY;

CREATE POLICY reports_source_state ON llm_reports.source_state TO reports_runtime USING (true) WITH CHECK (true);
CREATE POLICY reports_releases ON llm_reports.releases TO reports_runtime USING (true) WITH CHECK (true);
CREATE POLICY reports_report_versions ON llm_reports.report_versions TO reports_runtime USING (true) WITH CHECK (true);

COMMIT;
