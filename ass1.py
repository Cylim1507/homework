import pymysql
from datetime import datetime

def log_to_db(uid, status):
    try:
        # Connect to MySQL
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='your_root_password',
            database='rfid_logs'
        )

        with connection.cursor() as cursor:
            sql = "INSERT INTO logs (uid, status, timestamp) VALUES (%s, %s, %s)"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(sql, (uid, status, timestamp))

        connection.commit()
        print("Logged to database:", uid, status, timestamp)

    except pymysql.MySQLError as e:
        print("Error inserting into MySQL:", e)

    finally:
        connection.close()
