import json
import os

from kafka import KafkaProducer

from monitoring.checker import CheckResult, check
from monitoring.settings import build_settings, init_rules

TIMEOUT = 10


def result_serializer(result: CheckResult) -> bytes:
    return json.dumps({
        'response_time': result.response_time if result.response_time is not None else 'None',
        'status_code': result.status_code if result.status_code is not None else 'None',
        'regexp_result': result.regexp_result if result.regexp_result is not None else 'None',
        'failed': result.failed
    }).encode('utf-8')


def main():
    settings = build_settings()

    rules = init_rules(os.path.join(os.path.dirname(__file__), '..', 'tests', 'rules', 'one_rule.yaml'))
    results = [check(rule, TIMEOUT) for rule in rules]

    # With code snippets from https://help.aiven.io/en/articles/489572-getting-started-with-aiven-kafka
    ssl_cert_dir = os.path.join(os.path.dirname(__file__), '..', 'ssl_keys')
    producer = KafkaProducer(
        bootstrap_servers=settings['kafka']['url'],
        security_protocol='SSL',
        ssl_cafile=os.path.join(ssl_cert_dir, 'ca.pem'),
        ssl_certfile=os.path.join(ssl_cert_dir, 'service.cert'),
        ssl_keyfile=os.path.join(ssl_cert_dir, 'service.key'),
        value_serializer=result_serializer
    )
    for result in results:
        producer.send('monitoring-tests', result)
    producer.flush()
    print(results)


if __name__ == '__main__':
    main()
