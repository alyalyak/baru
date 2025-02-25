import machine
import time
import network
import dht
import urequests
import gc

# WiFi Credentials
WIFI_SSID = "PUSTAKA_106b"
WIFI_PASSWORD = "bacalah!"

# API Endpoint
API_URL = "http://192.168.19.95:5000/data"
UBIDOTS_URL = "https://industrial.api.ubidots.com/api/v1.6/devices/esp32/"

# Ubidots Token
UBIDOTS_TOKEN = "BBUS-wDcHFMhF5eS3jKFPduGCgPGxHkKtYo"
ubidot_headers = {"Content-Type": "application/json", "X-Auth-Token": UBIDOTS_TOKEN}

# Initialize Sensors
pir_sensor = machine.Pin(5, machine.Pin.IN)
dht_sensor = dht.DHT11(machine.Pin(4))

# Global Variables
motion_detected = False

# WiFi Connection
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(10):
        if wlan.isconnected():
            print("WiFi Connected:", wlan.ifconfig())
            return
        time.sleep(1)
    print("WiFi Connection Failed! Restarting ESP32...")
    machine.reset()

connect_wifi()

# PIR Interrupt Handler
def motion_callback(pin):
    global motion_detected
    motion_detected = True

pir_sensor.irq(trigger=machine.Pin.IRQ_RISING, handler=motion_callback)

# Send Data Function
def send_data(temp, hum, motion):
    data = {"temperature": temp, "humidity": hum, "motion": motion}
    for url, headers in [(API_URL, {}), (UBIDOTS_URL, ubidot_headers)]:
        for attempt in range(3):
            try:
                response = urequests.post(url, json=data, headers=headers, timeout=5)
                print(f"{url} Response: {response.status_code}")
                response.close()
                break
            except Exception as e:
                print(f"Error sending to {url} (Attempt {attempt+1}): {e}")
                time.sleep(2)

# Main Loop
while True:
    try:
        if motion_detected:
            dht_sensor.measure()
            temp, hum = dht_sensor.temperature(), dht_sensor.humidity()
            print(f"Temp: {temp}C, Hum: {hum}%, Motion Detected!")
            send_data(temp, hum, 1)
            motion_detected = False
    except Exception as e:
        print(f"General Error: {e}")
    time.sleep(0.01)
