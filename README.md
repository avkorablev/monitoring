# Simple website monitoring system using Kafka and PostgreSQL

***NB*** This project is a production-ready system. It is an attempt to learn how Kafka works and how I can use aiven.io
to run it. If you want to make it more robust, feel free to send your PRs.

## Setup

### Prepare environment

For this service, you have to have working Kafka and PostgreSQL services.

Create a new Kafka server in Aiven console. Download Access Key, Access Certificate, and CA Certificate files into 
certs folder. Create a new topic. 

Create a new PostgreSQL server in Aiven console. Execute `init_pg.sql` from sql folder using psql or any other software 
of your choice.

Copy setup-example.yaml to setup.yaml. Edit it using information from Aiven console.

### Prepare rules

All rules a placed in rules.yaml. You can use rules-example.yaml as a template for your one. Each rule consists of four 
fields: `url`, `period` (in seconds), `method` (`GET`, `POST` and other methods supported by requests library), 
regexp (a pattern that can be used in `re.compile` function).

## Manual start and tests

Services can be started manually. It should work with any Python version newer than 3.7. However, it was tested with 
Python 3.9 only.

To install dependencies:

```shell
pip install -Ur requirements.txt
```

To start worker:

```shell
python -m monitoring.worker
```

To start consumer:

```shell
python -m monitoring.consumer
```

There are several tests in the project. To start them:

```shell
pip install -Ur requirements-test.txt
pytest
```

## Docker

If you prefer to use docker, there is a docker-compose setup. 

```shell
docker-compose up
```