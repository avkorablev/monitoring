import os
from typing import Generator

import psycopg2
from kafka import KafkaConsumer
from psycopg2 import sql

from monitoring.checker import CheckResult, Rule
from monitoring.settings import build_settings, cert_files


def read_kafka_records(consumer: KafkaConsumer) -> Generator[CheckResult, None, None]:
        raw_msgs = consumer.poll(timeout_ms=1000)
        for tp, msgs in raw_msgs.items():
            for msg in msgs:
                print(msg.value)
                yield CheckResult.deserialize(msg.value)


if __name__ == '__main__':
    settings = build_settings()

    # With code snippets from https://help.aiven.io/en/articles/489572-getting-started-with-aiven-kafka
    ssl_cafile, ssl_certfile, ssl_keyfile = cert_files()
    consumer = KafkaConsumer(
        'monitoring-tests',
        auto_offset_reset='earliest',
        client_id='demo-client-1',
        group_id='demo-group',
        bootstrap_servers=settings['kafka']['url'],
        security_protocol='SSL',
        ssl_cafile=ssl_cafile,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
    )

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
                print("Received: {}".format(record))
                url, method, regexp = record.rule_id.split(':::')
                cursor.execute(
                    sql.SQL(
                        "select id from {}.{} where url = %s and method = %s and regexp = %s"
                    ).format(
                        sql.Identifier('monitoring'),
                        sql.Identifier('rules')
                    ),
                    [url, method, regexp]
                )
                if cursor.rowcount < 1:
                    print("Record id for {}:::{}:::{} not found".format(url, method, regexp))
                    continue
                rule_id = cursor.fetchone()[0]
                print()

                cursor.execute(
                    sql.SQL(
                        "insert into {}.{} "
                        "(utc_time, rule_id, response_time, status_code, regexp_result, failed) "
                        "values (%s, %s, %s, %s, %s, %s)"
                    ).format(
                        sql.Identifier('monitoring'),
                        sql.Identifier('checks')
                    ),
                    [record.utc_time, rule_id, record.response_time, record.status_code,
                     record.regexp_result, record.failed]
                )

        consumer.commit()
