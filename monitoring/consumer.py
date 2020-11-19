import os

from kafka import KafkaConsumer

from monitoring.settings import build_settings

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

    for _ in range(2):
        raw_msgs = consumer.poll(timeout_ms=1000)
        for tp, msgs in raw_msgs.items():
            for msg in msgs:
                print("Received: {}".format(msg.value))

    consumer.commit()
