import asyncio
import logging
import re
from typing import Set

from kafka import KafkaProducer
from psycopg2 import sql

from monitoring.checker import Rule, check, utcnow
from monitoring.gp import get_pg_connection
from monitoring.settings import build_settings, cert_files, init_rules

logger = logging.getLogger(__name__)

TIMEOUT = 10


SELECT_RULE = sql.SQL('''
select id, url, period, method, regexp from monitoring.rules 
left join monitoring.lock on rules.id = lock.rule_id
where lock.last_start is null 
    or timezone('UTC'::text, now()) - interval '1 second' * rules.period >= lock.last_start
limit 1
''')


ACQUIRE_LOCK = sql.SQL('''
insert into monitoring.lock values (%s, %s, %s)
on conflict (rule_id) do update set last_start = %s
''')

INSERT_RULES = sql.SQL(
    "insert into monitoring.rules "
    "(url, period, method, regexp) "
    "values (%s, %s, %s, %s) "
    "on conflict do nothing"
)


async def worker(name: str, producer: KafkaProducer, topic: str, settings):
    while True:
        with get_pg_connection(settings) as pg_connection:
            rule_id = None
            rule = None
            with pg_connection.cursor() as cur:
                cur.execute(SELECT_RULE)
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
                    cur.execute(ACQUIRE_LOCK, [rule_id, current_start, name, current_start])
                    pg_connection.commit()
                    if cur.rowcount > 0:
                        logger.info('%s is processing %s', name, rule)
                        producer.send(topic, check(rule, TIMEOUT))

        await asyncio.sleep(1)


def upload_rules(rules: Set[Rule], pg_connection):
    with pg_connection.cursor() as cur:
        for rule in rules:
            cur.execute(INSERT_RULES, [rule.url, rule.period, rule.method, str(rule.regexp.pattern)])


# With code snippets from https://help.aiven.io/en/articles/489572-getting-started-with-aiven-kafka
def get_producer(settings):
    ssl_cafile, ssl_certfile, ssl_keyfile = cert_files()
    return KafkaProducer(
        bootstrap_servers=settings['kafka']['url'],
        security_protocol='SSL',
        ssl_cafile=ssl_cafile,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
        value_serializer=lambda v: v.serialize()
    )


async def main():
    settings = build_settings()
    rules = init_rules()

    with get_pg_connection(settings) as pg_connection:
        upload_rules(rules, pg_connection)

    producer = get_producer(settings)

    tasks = []
    for i in range(settings['kafka']['worker']['num_tasks']):
        task = asyncio.create_task(worker(f'worker-{i}', producer, settings['kafka']['topic'], settings))
        tasks.append(task)

    try:
        [await t for t in tasks]
    finally:
        for task in tasks:
            task.cancel()
        producer.flush()

if __name__ == '__main__':
    asyncio.run(main())
