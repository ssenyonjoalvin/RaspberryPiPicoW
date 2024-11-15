import time
import machine
import network
import ujson
from umqtt.simple import MQTTClient #need to install this library
import ssl

#ssid = 'Luban Lab'
#password = 'Domo@1234'

SSID = 'sunbird'
PASS = 'ltd@sunbird.ai'


CLIENT_ID = "Smart_bus_transportation" #name of your thing
AWS_ENDPOINT = "a2jsx9uhuycxqp-ats.iot.eu-north-1.amazonaws.com" #include you AWS Endpoint here

#topic to which the device publishes data. 
PUB_TOPIC = 'occupancy/light'


#subscribe to a topic
SUB_TOPIC = 'ocupancy/pin_state'

# Paths to the certificate files. Need to convert certificate files to DER format. Micropython requires der files
ROOT_CA_PATH = "AmazonRootCA1.der"#include your rootCA1 here. need to convert it to .der format #openssl x509 -in rootCA1.pem -outform der -out rootCA1.der
CERT_PATH = "proj-certificate.der" #include your client_cert path here in .der format #openssl x509 -in client_cert.pem -outform der -out client_cert.der
KEY_PATH = "proj-private.der"#include your private_key.der path here #openssl pkey -in private_key.pem -out private_key2.der -outform DER 

# Reading Thing Private Key and Certificate into variables for later use
with open(KEY_PATH, 'rb') as f:
    DEV_KEY = f.read()
# Thing Certificate
with open(CERT_PATH, 'rb') as f:
    DEV_CRT = f.read()

# Define light (Onboard Green LED) and set its default state to off
light = machine.Pin("LED", machine.Pin.OUT)
light.off()

pin = machine.Pin(15, machine.Pin.OUT)  # Choose GPIO 15 to be controlled
pin.off()

# Wifi Connection Setup
def wifi_connect():
    print('Connecting to wifi...')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASS)
    while wlan.isconnected() == False:
        light.on()
        print('Waiting for connection...')
        time.sleep(0.5)
        light.off()
        time.sleep(0.5)
    print('Connection details: %s' % str(wlan.ifconfig()))


# Function to publish the pin's state back to AWS IoT
def report_pin_state(light_pin_state, pin_15_state):
    message = b'{"Light":"%s","Pin 15":"%s"}' % (light_pin_state,pin_15_state)
    print('Reporting pin state:', message)
    mqtt.publish(topic=PUB_TOPIC, msg=message, qos=0)


#publish to topic "pi/pin_state" to change pin state
# {
  # "state": "on"
# }

# Callback function for all subscriptions
def mqtt_subscribe_callback(topic, msg):
    # Decode the topic from bytes to string
    topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')
    print("Received\n topic: %s \nmessage: %s" % (topic, msg))
    if topic == SUB_TOPIC:
        mesg = ujson.loads(msg)
        if 'state' in mesg.keys():
            if mesg['state'] == 'on' or mesg['state'] == 'ON' or mesg['state'] == 'On':
                light.on()
                print('Light is ON')
                pin.on()
                print('Pin 15 is ON')
                # Report the pin state back
                report_pin_state('on','on')
            else:
                light.off()
                print('Light is OFF')
                pin.off()
                print('Pin 15 is OFF')
                # Report the pin state back
                report_pin_state('off','off')
            

# Read current temperature from RP2040 embeded sensor
def get_rpi_temperature():
    sensor = machine.ADC(4)
    voltage = sensor.read_u16() * (3.3 / 65535)
    temperature = 27 - (voltage - 0.706) / 0.001721
    return temperature

wifi_connect()

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.verify_mode = ssl.CERT_REQUIRED  # Change to CERT_REQUIRED for better security
context.load_verify_locations(ROOT_CA_PATH)  # Load root CA
context.load_cert_chain(certfile=DEV_CRT, keyfile=DEV_KEY)  # Load client cert and key

mqtt = MQTTClient(
    client_id=CLIENT_ID,
    server=AWS_ENDPOINT,
    port=8883,
    keepalive=5000,
    ssl=context)

# Establish connection to AWS IoT Core
print('Connecting to AWS...')
mqtt.connect()
print('Connected to AWS')

# Set callback for subscriptions
mqtt.set_callback(mqtt_subscribe_callback)

# Subscribe to topic
print(f"Subscribing to {SUB_TOPIC}...")
mqtt.subscribe(SUB_TOPIC)
print(f"Subscribed to {SUB_TOPIC}")

# Main loop - with 5 sec delay
while True:
    # Publisg the temperature
    message = b'{"temperature":%s, "temperature_unit":"Degrees Celsius"}' % get_rpi_temperature()
    print('Publishing topic %s message %s' % (PUB_TOPIC, message))
    # QoS (Quality of Service) Levels: MQTT supports three levels of message delivery guarantees:
    # QoS 0 (At most once): Messages are delivered at most once, without retry if the client misses it. This is the most lightweight but risky in terms of missing messages.
    # QoS 1 (At least once): Messages are delivered at least once. The broker will keep trying to send the message until the client acknowledges it.
    # QoS 2 (Exactly once): The most reliable, ensures that messages are delivered exactly once by keeping track of each message, but has more overhead.
    # If you’re using QoS 0, you must poll more frequently because missed messages are not retained.
    # If the interval is too short, your device might consume more power, especially for battery-powered IoT devices like the Pico W.
    # See https://docs.aws.amazon.com/iot/latest/developerguide/mqtt.html
    mqtt.publish(topic=PUB_TOPIC, msg=message, qos=0)

    # Check subscriptions for message
    mqtt.check_msg()
    time.sleep(10)