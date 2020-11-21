CREATE SCHEMA IF NOT EXISTS monitoring;

CREATE TABLE IF NOT EXISTS monitoring.checks (
    utc_time timestamp NOT NULL,
    rule_id char,
    response_time float,
    status_code int,
    regexp_result bool,
    failed bool NOT NULL,
    CONSTRAINT rule_id_utc_time PRIMARY KEY (rule_id, utc_time)
);

CREATE INDEX IF NOT EXISTS rule_id ON monitoring.checks (rule_id);
CREATE INDEX IF NOT EXISTS utc_time ON monitoring.checks (utc_time);