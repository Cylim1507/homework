import paho.mqtt.client as mqtt
import pymysql

# Database connection
dbConn = pymysql.connect("localhost","pi","","temp")

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("/edge_device/data")  # Subscribe to the MQTT topic

def on_message(client, userdata, msg):
    # Split the message to extract the timestamp and the MQTT message
    data = msg.payload.decode("utf-8")
    timestamp, mqtt_message = data.split(" - ", 1)
    
    # Insert into the database
    with dbConn:
        cursor = dbConn.cursor()
        cursor.execute("INSERT INTO mqtt_data (timestamp, message) VALUES (%s, %s)", (timestamp, mqtt_message))
        dbConn.commit()

# MQTT client setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect("test.mosquitto.org", 1883, 60)

# Keep the client running
client.loop_forever()
