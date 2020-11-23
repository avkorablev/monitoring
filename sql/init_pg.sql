CREATE SCHEMA IF NOT EXISTS monitoring;

CREATE TABLE IF NOT EXISTS monitoring.rules (
                                                id serial PRIMARY KEY,
                                                url varchar,
                                                period int,
                                                method varchar,
                                                regexp varchar,
                                                CONSTRAINT unique_key UNIQUE (url, method, regexp)
);

CREATE TABLE IF NOT EXISTS monitoring.lock (
                                               rule_id int,
                                               last_start timestamp,
                                               worker varchar,
                                               CONSTRAINT rule_id UNIQUE (rule_id),
                                               FOREIGN KEY (rule_id) REFERENCES monitoring.rules (id)
);

CREATE INDEX IF NOT EXISTS rule_id ON monitoring.lock (rule_id);

CREATE TABLE IF NOT EXISTS monitoring.checks (
                                                 utc_time timestamp NOT NULL,
                                                 rule_id int,
                                                 response_time float,
                                                 status_code int,
                                                 regexp_result bool,
                                                 failed bool NOT NULL,
                                                 CONSTRAINT rule_id_utc_time PRIMARY KEY (rule_id, utc_time),
                                                 FOREIGN KEY (rule_id) REFERENCES monitoring.rules (id)
);

CREATE INDEX IF NOT EXISTS rule_id ON monitoring.checks (rule_id);
CREATE INDEX IF NOT EXISTS utc_time ON monitoring.checks (utc_time);