import psycopg2


def get_pg_connection(host, port, database, user, password, sslmode):
    return psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        sslmode=sslmode,
    )
