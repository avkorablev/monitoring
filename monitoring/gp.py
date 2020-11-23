import psycopg2


def get_pg_connection(settings):
    return psycopg2.connect(
        host=settings['pg']['host'],
        port=settings['pg']['port'],
        database=settings['pg']['database'],
        user=settings['pg']['user'],
        password=settings['pg']['password'],
        sslmode=settings['pg']['sslmode'],
    )
