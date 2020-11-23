import logging
from typing import Generator

import psycopg2
from kafka import KafkaConsumer
from psycopg2 import sql

from .checker import CheckResult
from .settings import build_settings, cert_files


logger = logging.getLogger(__name__)


SELECT_RULE = sql.SQL('select id from monitoring.rules where url = %s and method = %s and regexp = %s')


INSERT_CHECK_RESULT = sql.SQL(
    'insert into monitoring.checks '
    '(utc_time, rule_id, response_time, status_code, regexp_result, failed) '
    'values (%s, %s, %s, %s, %s, %s)'
)


def read_kafka_records(consumer: KafkaConsumer) -> Generator[CheckResult, None, None]:
    raw_msgs = consumer.poll(timeout_ms=1000)
    for tp, msgs in raw_msgs.items():
        for msg in msgs:
            yield CheckResult.deserialize(msg.value)


# With code snippets from https://help.aiven.io/en/articles/489572-getting-started-with-aiven-kafka
def get_consumer(settings):
    ssl_cafile, ssl_certfile, ssl_keyfile = cert_files()
    return KafkaConsumer(
        settings['kafka']['topic'],
        auto_offset_reset='earliest',
        client_id=settings['kafka']['consumer']['client_id'],
        group_id=settings['kafka']['consumer']['group_id'],
        bootstrap_servers=settings['kafka']['url'],
        security_protocol='SSL',
        ssl_cafile=ssl_cafile,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
    )


def main():
    settings = build_settings()
    consumer = get_consumer(settings)
    while True:
        with psycopg2.connect(
                host=settings['pg']['host'],
                port=settings['pg']['port'],
                database=settings['pg']['database'],
                user=settings['pg']['user'],
                password=settings['pg']['password'],
                sslmode=settings['pg']['sslmode'],
        ) as connection, connection.cursor() as cursor:
            for record in read_kafka_records(consumer):
                logger.debug("Received: %s", record)
                url, method, regexp = record.rule_id.split(':::')
                cursor.execute(SELECT_RULE, [url, method, regexp])
                if cursor.rowcount < 1:
                    logger.warning("Record id for %s not found", record.rule_id)
                    continue
                rule_id = cursor.fetchone()[0]
                cursor.execute(
                    INSERT_CHECK_RESULT,
                    [record.utc_time, rule_id, record.response_time, record.status_code,
                     record.regexp_result, record.failed]
                )

        consumer.commit()


if __name__ == '__main__':
    main()
