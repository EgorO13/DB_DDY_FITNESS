import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

connection = None

try:
    connection = psycopg2.connect(
        host="localhost",
        database="postgres", # Подключаемся к postgres, чтобы управлять другими БД
        user="postgres",
        password="261022",
        port="5432",
    )
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    with connection.cursor() as cursor:
        print("Пересоздаем целевую базу данных...")
        cursor.execute("DROP DATABASE IF EXISTS ddy_fitness;")
        cursor.execute("CREATE DATABASE ddy_fitness;")
        print("Чистая база данных ddy_fitness успешно создана!")

except Exception as error:
    print("Ошибка:", error)

finally:
    if connection:
        connection.close()
