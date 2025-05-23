import pymysql

# Connect to the database
dbConn = pymysql.connect("localhost","pi","","temp")
cursor = dbConn.cursor()

# Create a table for storing MQTT messages with timestamps
cursor.execute("""
    CREATE TABLE IF NOT EXISTS mqtt_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp VARCHAR(20),  # Store timestamp as a string
        message TEXT  # Store the MQTT message
    )
""")

dbConn.commit()
cursor.close()
