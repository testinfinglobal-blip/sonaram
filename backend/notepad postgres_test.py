import psycopg

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "myai"
DB_USER = "postgres"

DB_PASSWORD = "Test@123"

try:
    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    print("PostgreSQL connection successful!")

    connection.close()

except Exception as error:
    print("PostgreSQL connection failed:")
    print(error)s