import time
import machine
import network
import ujson
from umqtt.simple import MQTTClient #need to install this library
import ssl


# Wifi details
SSID = 'sunbird'
PASS = 'ltd@sunbird.ai'

CLIENT_ID = "Smart_bus_transportation"  # name of your thing
AWS_ENDPOINT = "a2jsx9uhuycxqp-ats.iot.eu-north-1.amazonaws.com"  # AWS Endpoint

# Topics
PUB_TOPIC = 'occupancy/light'
SUB_TOPIC = 'ocupancy/pin_state'

# Paths to certificate files
ROOT_CA_PATH = "AmazonRootCA1.der"  # Root CA file in DER format
CERT_PATH = "proj-certificate.der"  # Client certificate in DER format
KEY_PATH = "proj-private.der"  # Private key in DER format

# Sensor and pin initialization
light = machine.Pin("LED", machine.Pin.OUT)
light.off()

pin = machine.Pin(15, machine.Pin.OUT)  # Choose GPIO 15 to be controlled
pin.off()

infrared_sensor = machine.Pin(16, machine.Pin.IN)  # IR sensor on GPIO 16
ldr = machine.ADC(27)  # LDR sensor on GPIO 27
led2 = machine.Pin(17, machine.Pin.OUT)  # LED for LDR intensity control

# Wifi Connection Setup
def wifi_connect():
    print('Connecting to wifi...')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASS)
    while not wlan.isconnected():
        light.on()
        print('Waiting for connection...')
        time.sleep(0.5)
        light.off()
        time.sleep(0.5)
    print('Connection details: %s' % str(wlan.ifconfig()))

# Function to report sensor states to AWS, with timestamp added
def report_sensor_data(infrared_sensor_value, ldr_value, temperature):
    # Manually construct timestamp
    current_time = time.localtime()
    timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        current_time[0], current_time[1], current_time[2],  # year, month, day
        current_time[3], current_time[4], current_time[5]   # hour, minute, second
    )
    message = ujson.dumps({
        "Timestamp": timestamp,  # Add the timestamp
        "IR_Sensor": infrared_sensor_value,
        "LDR_Value": ldr_value,
        "Temperature": temperature,
    })
    print('Reporting sensor data:', message)
    mqtt.publish(topic=PUB_TOPIC, msg=message, qos=0)

# Callback function for subscriptions
def mqtt_subscribe_callback(topic, msg):
    topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')
    print("Received\n topic: %s \nmessage: %s" % (topic, msg))
    if topic == SUB_TOPIC:
        mesg = ujson.loads(msg)
        if 'state' in mesg.keys():
            if mesg['state'] in ['on', 'ON', 'On']:
                light.on()
                print('Light is ON')
                pin.on()
                print('Pin 15 is ON')
                report_pin_state('on', 'on')
            else:
                light.off()
                print('Light is OFF')
                pin.off()
                print('Pin 15 is OFF')
                report_pin_state('off', 'off')

# Read current temperature from RP2040 embedded sensor
def get_rpi_temperature():
    sensor = machine.ADC(4)
    voltage = sensor.read_u16() * (3.3 / 65535)
    temperature = 27 - (voltage - 0.706) / 0.001721
    return temperature

# Connect to wifi
wifi_connect()

# SSL context for secure connection
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.verify_mode = ssl.CERT_REQUIRED
context.load_verify_locations(ROOT_CA_PATH)
context.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)

# Initialize MQTT client
mqtt = MQTTClient(
    client_id=CLIENT_ID,
    server=AWS_ENDPOINT,
    port=8883,
    keepalive=5000,
    ssl=context)

# Connect to AWS IoT Core
print('Connecting to AWS...')
mqtt.connect()
print('Connected to AWS')

# Set callback for subscriptions
mqtt.set_callback(mqtt_subscribe_callback)

# Subscribe to topic
mqtt.subscribe(SUB_TOPIC)
print(f"Subscribed to {SUB_TOPIC}")

# Main loop
while True:
    # Get sensor readings
    infrared_sensor_value = infrared_sensor.value()  # IR sensor reading
    ldr_value = ldr.read_u16()  # LDR sensor reading
    
    # Edge computing based on LDR value
    if ldr_value > 330:
        led2.value(1)
    else:
        led2.value(0)
    
    # Get temperature from the embedded sensor
    temperature = get_rpi_temperature()

    # Print the values for debugging
    print(f"IR Sensor Value: {infrared_sensor_value}, LDR Value: {ldr_value}, Temperature: {temperature}°C")

    # Report data to AWS
    report_sensor_data(infrared_sensor_value, ldr_value, temperature)

    # Check for any messages from the subscribed topic
    mqtt.check_msg()
    
    # Delay between readings
    time.sleep(2)
