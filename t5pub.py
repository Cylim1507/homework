import serial
import paho.mqtt.publish as publish
import datetime

ser = serial.Serial('/dev/ttyS0', 9600)

while True:
    line = ser.readline().rstrip()
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current timestamp
    message = f"{current_time} - {line}"  # Combine timestamp with sensor data
    publish.single("/edge_device/data", message, hostname="test.mosquitto.org")
