import asyncio
import os

from kafka import KafkaProducer

from monitoring.checker import check
from monitoring.settings import build_settings, init_rules

TIMEOUT = 10


async def worker(name: str, queue: asyncio.Queue, producer: KafkaProducer, topic: str):
    while True:
        rule = await queue.get()
        print(f'{name} is processing {rule}')
        producer.send(topic, check(rule, TIMEOUT))
        await asyncio.sleep(rule.period)
        queue.put_nowait(rule)
        queue.task_done()
        print(f'{name} has reposted {rule}')
        print(f'{queue.empty()}')


async def main():
    settings = build_settings()

    rules = init_rules(os.path.join(os.path.dirname(__file__), '..', 'tests', 'rules', 'one_rule.yaml'))

    # With code snippets from https://help.aiven.io/en/articles/489572-getting-started-with-aiven-kafka
    ssl_cert_dir = os.path.join(os.path.dirname(__file__), '..', 'ssl_keys')
    producer = KafkaProducer(
        bootstrap_servers=settings['kafka']['url'],
        security_protocol='SSL',
        ssl_cafile=os.path.join(ssl_cert_dir, 'ca.pem'),
        ssl_certfile=os.path.join(ssl_cert_dir, 'service.cert'),
        ssl_keyfile=os.path.join(ssl_cert_dir, 'service.key'),
        value_serializer=lambda v: v.serialize()
    )

    # https://docs.python.org/3/library/asyncio-queue.html#asyncio-queues
    queue = asyncio.Queue()
    for rule in rules:
        queue.put_nowait(rule)

    tasks = []
    for i in range(3):
        task = asyncio.create_task(worker(f'worker-{i}', queue, producer, 'monitoring-tests'))
        tasks.append(task)

    try:
        await queue.join()
    except Exception as e:
        raise
    finally:
        for task in tasks:
            task.cancel()
        producer.flush()

if __name__ == '__main__':
    asyncio.run(main())
