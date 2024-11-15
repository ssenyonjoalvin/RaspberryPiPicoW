from umqtt.simple import MQTTClient
import network
import socket
from time import sleep
from picozero import pico_temp_sensor, pico_led
import time
import json
import machine  # For device-specific control, if needed

#wifi credentials
ssid = 'sunbird'
password = 'ltd@sunbird.ai'

def connect():
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection


# Set up MQTT client
client = MQTTClient(
    client_id="Smart_bus_transportation",
    server="a2jsx9uhuycxqp-ats.iot.eu-north-1.amazonaws.com",
    port=8883,
    ssl=True
)

# Connect to AWS IoT
try:
    client.connect()
    print("Connected to AWS IoT")
except Exception as e:
    print("Failed to connect to AWS IoT:", e)

# Publish data loop
try:
    while True:
        temperature = 20 + (5 * (time.time() % 10) / 10)  # Simulated temperature
        humidity = 40 + (20 * (time.time() % 10) / 10)     # Simulated humidity
        data = {"temperature": temperature, "humidity": humidity}
        
        client.publish("sensor/data", json.dumps(data))
        print(f"Published: {data}")
        
        time.sleep(5)  # Publish every 5 seconds

except KeyboardInterrupt:
    print("Stopped by user")
except Exception as e:
    print("An error occurred:", e)
finally:
    client.disconnect()
    print("Disconnected from AWS IoT")
