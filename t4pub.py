import paho.mqtt.publish as publish
publish.single("/edge_device/data", "this is a message", hostname="test.mosquitto.org")