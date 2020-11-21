import os
from typing import Generator

import psycopg2
from kafka import KafkaConsumer
from psycopg2 import sql

from monitoring.checker import CheckResult
from monitoring.settings import build_settings


def read_kafka_records(consumer: KafkaConsumer) -> Generator[CheckResult, None, None]:
        raw_msgs = consumer.poll(timeout_ms=1000)
        for tp, msgs in raw_msgs.items():
            for msg in msgs:
                yield CheckResult.deserialize(msg.value)


if __name__ == '__main__':
    settings = build_settings()

    # With code snippets from https://help.aiven.io/en/articles/489572-getting-started-with-aiven-kafka
    ssl_cert_dir = os.path.join(os.path.dirname(__file__), '..', 'ssl_keys')
    consumer = KafkaConsumer(
        'monitoring-tests',
        auto_offset_reset='earliest',
        client_id='demo-client-1',
        group_id='demo-group',
        bootstrap_servers=settings['kafka']['url'],
        security_protocol='SSL',
        ssl_cafile=os.path.join(ssl_cert_dir, 'ca.pem'),
        ssl_certfile=os.path.join(ssl_cert_dir, 'service.cert'),
        ssl_keyfile=os.path.join(ssl_cert_dir, 'service.key'),
    )

    connection = psycopg2.connect(
        host=settings['pg']['host'],
        port=settings['pg']['port'],
        database=settings['pg']['database'],
        user=settings['pg']['user'],
        password=settings['pg']['password'],
        sslmode=settings['pg']['sslmode'],
    )
    cursor = connection.cursor()

    while True:
        for record in read_kafka_records(consumer):
            print("Received: {}".format(record))
            cursor.execute(
                sql.SQL(
                    "insert into {}.{} "
                    "(utc_time, rule_id, response_time, status_code, regexp_result, failed) "
                    "values (%s, %s, %s, %s, %s, %s)"
                ).format(
                    sql.Identifier('monitoring'),
                    sql.Identifier('checks')
                ),
                [record.utc_time, record.rule_id, record.response_time, record.status_code,
                 record.regexp_result, record.failed]
            )

        connection.commit()
        consumer.commit()
