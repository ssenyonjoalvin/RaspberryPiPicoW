      
import machine
import utime
reed = machine.Pin(16, machine.Pin.IN)
led = machine.Pin(17, machine.Pin.OUT)
while True:
    value = reed.value()
    print(f"Sensor Value: {value}")
    print(f"nothing detected yet")
    
    if value == 0:
        led.value(1)
        print("IR Sensor Detected something entering the bus!")
    else:
        led.value(0)
    
    utime.sleep(0.8)  # Increase the sleep duration to check if it helps
