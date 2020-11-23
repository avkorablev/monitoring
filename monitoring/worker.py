import asyncio
import os
import re
from typing import Set

from kafka import KafkaProducer
from psycopg2 import sql

from monitoring.checker import Rule, check, utcnow
from monitoring.gp import get_pg_connection
from monitoring.settings import build_settings, cert_files, init_rules

TIMEOUT = 10


SELECT_RULE = sql.SQL('''
select id, url, period, method, regexp from {schema}.{rules} 
left join {schema}.{lock} on {rules}.id = {lock}.rule_id
where {lock}.last_start is null 
    or timezone('UTC'::text, now()) - interval '1 second' * {rules}.period >= {lock}.last_start
limit 1
''').format(schema=sql.Identifier('monitoring'), rules=sql.Identifier('rules'), lock=sql.Identifier('lock'))


ACQUIRE_LOCK = sql.SQL('''
insert into {schema}.{lock} values (%s, %s, %s)
on conflict (rule_id) do update set last_start = %s
''').format(schema=sql.Identifier('monitoring'), lock=sql.Identifier('lock'))


async def worker(name: str, producer: KafkaProducer, topic: str, settings):
    while True:
        with get_pg_connection(
                host=settings['pg']['host'],
                port=settings['pg']['port'],
                database=settings['pg']['database'],
                user=settings['pg']['user'],
                password=settings['pg']['password'],
                sslmode=settings['pg']['sslmode'],
        ) as pg_connection:
            rule_id = None
            rule = None
            with pg_connection.cursor() as cur:
                cur.execute(
                    SELECT_RULE
                )
                if cur.rowcount > 0:
                    result = cur.fetchone()
                    rule_id = result[0]
                    rule = Rule(
                        url=result[1],
                        period=result[2],
                        method=result[3],
                        regexp=re.compile(result[4])
                    )

            with pg_connection.cursor() as cur:
                if rule:
                    current_start = utcnow()
                    cur.execute(
                        ACQUIRE_LOCK,
                        [rule_id, current_start, name, current_start]
                    )
                    pg_connection.commit()
                    if cur.rowcount > 0:
                        print(f'{name} is processing {rule}')
                        producer.send(topic, check(rule, TIMEOUT))

        await asyncio.sleep(1)


def upload_rules(rules: Set[Rule], pg_connection):
    cur = pg_connection.cursor()
    for rule in rules:
        cur.execute(
            sql.SQL(
                "insert into {}.{} "
                "(url, period, method, regexp) "
                "values (%s, %s, %s, %s) "
                "on conflict do nothing"
            ).format(
                sql.Identifier('monitoring'),
                sql.Identifier('rules')
            ),
            [rule.url, rule.period, rule.method, str(rule.regexp.pattern)]
        )
    pg_connection.commit()


async def main():
    settings = build_settings()
    rules = init_rules(os.path.join(os.path.dirname(__file__), '..', 'rules.yaml'))

    with get_pg_connection(
        host=settings['pg']['host'],
        port=settings['pg']['port'],
        database=settings['pg']['database'],
        user=settings['pg']['user'],
        password=settings['pg']['password'],
        sslmode=settings['pg']['sslmode'],
    ) as pg_connection:
        upload_rules(rules, pg_connection)

    # With code snippets from https://help.aiven.io/en/articles/489572-getting-started-with-aiven-kafka
    ssl_cafile, ssl_certfile, ssl_keyfile = cert_files()
    producer = KafkaProducer(
        bootstrap_servers=settings['kafka']['url'],
        security_protocol='SSL',
        ssl_cafile=ssl_cafile,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
        value_serializer=lambda v: v.serialize()
    )

    tasks = []
    for i in range(3):
        task = asyncio.create_task(worker(f'worker-{i}', producer, 'monitoring-tests', settings))
        tasks.append(task)

    [await t for t in tasks]

    for task in tasks:
        task.cancel()
    producer.flush()

if __name__ == '__main__':
    asyncio.run(main())
