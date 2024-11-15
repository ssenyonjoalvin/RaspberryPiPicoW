import network
import socket
from time import sleep
from picozero import pico_temp_sensor, pico_led
import machine

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


def webpage(temperature, state):
    # Template HTML
    html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Document</title>
            </head>
            <body>
                <form action="./lighton">
                    <input type="submit" value="Light on" />
                </form>

                <form action="./lightoff">
                    <input type="submit" value="Light off" />
                </form>

                <p>LED is {state}</p>
                <p>Temperature is {temperature}</p>
            </body>
            </html>
            """
    return str(html)


def serve(connection):
    # Start a web server
    state = 'OFF'
    pico_led.off()
    temperature = 0
    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)
        try:
            request = request.split()[1]
        except IndexError:
            pass
        if request == '/lighton?':
            pico_led.on()
            state = 'ON'
            temperature = pico_temp_sensor.temp
        elif request =='/lightoff?':
            pico_led.off()
            state = 'OFF'
           # temperature = pico_temp_sensor.temp
        print(request)
        
        html = webpage(temperature, state)
        client.send(html)
        
        client.close()


try:
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except KeyboardInterrupt:
    machine.reset()