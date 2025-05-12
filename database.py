import serial
import pymysql

device = '/dev/ttyS0'

# Connect to the Arduino
arduino = serial.Serial(device, 9600)
data = arduino.readline().decode('utf-8').strip()  # Decode bytes to string

print("Read from Arduino:", data)

# Connect to the database
try:
    dbConn = pymysql.connect(host="localhost", user="kali", password="", database="temperature_db")
except pymysql.MySQLError as e:
    print("Database connection failed:", e)
    exit()

print("Database connected:", dbConn)

# Insert data into the database
try:
    with dbConn.cursor() as cursor:
        cursor.execute("INSERT INTO templog (temperature) VALUES (%s)", (data,))
        dbConn.commit()
        print("Data inserted successfully.")
except pymysql.MySQLError as e:
    print("Failed to insert data:", e)
finally:
    dbConn.close()
