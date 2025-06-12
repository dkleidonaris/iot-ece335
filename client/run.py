import time
import board
import busio
import random
import threading
import socket
import logging
import RPi.GPIO as GPIO
import adafruit_ahtx0
import paho.mqtt.client as mqtt
from os import getenv
from dotenv import load_dotenv
from influxdb import InfluxDBClient
import json

LOGGING: str = "console"
LOG_FILE: str = "stats.log"

LED_PIN: int = 17

load_dotenv()

PUBLISH_INTERVAL = int(getenv('PUBLISH_INTERVAL'))

influxdb_client = InfluxDBClient(
    host=getenv('INFLUX_URL'),
    port=getenv('INFLUX_PORT'),
    username=getenv('INFLUX_USERNAME'),
    password=getenv('INFLUX_PASSWORD'),
    database=getenv('INFLUX_DB')
  )

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_ahtx0.AHTx0(i2c)

broker_address = getenv('MQTT_SERVER')
broker_port = int(getenv('MQTT_PORT'))
topic = getenv('MQTT_TOPIC')
client_id = getenv('CLIENT_ID')

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"client_{random.randint(0, 1000)}")
mqtt_client.username_pw_set(getenv('MQTT_USERNAME'), getenv("MQTT_PASSWORD"))

mqtt_client.connect(broker_address, broker_port)
mqtt_client.loop_start()

def config_gpio() -> None:
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(LED_PIN, GPIO.OUT)
  GPIO.output(LED_PIN, GPIO.LOW)

def config_logging() -> None:
  logging.basicConfig(
    filename=LOG_FILE,
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
  )

def send_measurements() -> tuple[float, float]:
  if LOGGING == "file":
    logging.debug("Getting AHTx0 sensor measurements...")
  
  temperature = sensor.temperature
  humidity = sensor.relative_humidity

  payload = json.dumps({
    "client_id": client_id,
    "temperature": round(temperature, 2),
    "humidity": round(humidity, 2)
  })
  
  topic_final = f"{topic}/measurements"
  print(f"Publishing to {topic_final}")
  mqtt_client.publish(topic_final, payload, qos=1)

  if LOGGING == "console":
    print(f"Temperature: {temperature:.2f} °C")
    print(f"Humidity: {humidity:.2f} %")
  else:
    logging.info(f"Temperature: {temperature:.2f} °C")
    logging.info(f"Humidity: {humidity:.2f} %")

  return temperature, humidity

def register_client():
  client_id = getenv('CLIENT_ID')
  lat = float(getenv('DEVICE_LAT'))
  lng = float(getenv('DEVICE_LNG'))
  timezone = getenv('DEVICE_TIMEZONE')
    
  json_body = [{
    "measurement": "devices",
    "tags": {
      "client_id": client_id
    },
    "time": "1970-01-01T00:00:00Z",
    "fields": {"lat": lat, "lng": lng, "timezone": timezone}
  }]
  
  influxdb_client.write_points(json_body)
  
def send_thread():
  try:
    while True:
      temperature, humidity = send_measurements()
      
      time.sleep(PUBLISH_INTERVAL)
  except KeyboardInterrupt:
    GPIO.cleanup()
    
    if LOGGING == "console":
      print("Received Ctrl+C signal! Bye")
    else:
      logging.info("Received Ctrl+C signal! Bye")

  finally:
    mqtt_client.loop_stop()  # Stop the background MQTT loop
    mqtt_client.disconnect()  # Disconnect from the broker
    
def check_watering(client, userdata, msg):
  data = json.loads(msg.payload.decode())
  
  if(data['client_id'] == getenv('CLIENT_ID')):
    GPIO.output(LED_PIN, GPIO.HIGH)
    
    time.sleep(10)
    
    GPIO.output(LED_PIN, GPIO.LOW)

    
def receive_thread():
  client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"client_{random.randint(0, 1000)}")
  client.username_pw_set(getenv('MQTT_USERNAME'), getenv("MQTT_PASSWORD"))
  
  client.on_message = check_watering

  client.connect(broker_address, broker_port)
  topic_final = f"{topic}/decisions"
  client.subscribe(topic_final)

  print(f"Subscribing to `{topic_final}`. Waiting for messages...")
  client.loop_forever()

def main() -> None:
  config_gpio()
  
  register_client()
  
  thread1 = threading.Thread(target=send_thread, daemon=True)
  thread2 = threading.Thread(target=receive_thread, daemon=True)

  thread1.start()
  thread2.start()

  try:
      while True:
          time.sleep(1)
  except KeyboardInterrupt:
      print("Received Ctrl+C. Exiting...")

if __name__ == "__main__":
  main()
  exit(0)
