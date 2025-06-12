from flask import Flask, request, jsonify
import random
import requests
from datetime import datetime, timedelta
from datetime import timezone as timezone_lib
import time
import pytz
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from os import getenv
from dotenv import load_dotenv
from neural_network.predict import predict
from influxdb import InfluxDBClient
import json
import threading
import paho.mqtt.client as mqtt

load_dotenv()

influxdb_client = InfluxDBClient(
    host=getenv('INFLUX_URL'),
    port=getenv('INFLUX_PORT'),
    username=getenv('INFLUX_USERNAME'),
    password=getenv('INFLUX_PASSWORD'),
    database=getenv('INFLUX_DB')
  )

broker_address = getenv('MQTT_SERVER')
broker_port = int(getenv('MQTT_PORT'))
topic = getenv('MQTT_TOPIC')
client_id = "server"

def get_weather_params(lat, lng, timezone):
    url = getenv('WEATHER_API_URL')
    
    params = {
        "latitude": lat,
        "longitude": lng,
        "timezone": timezone,
        "daily": "sunshine_duration",
        "hourly": "precipitation_probability",
        "forecast_days": 1,
        "forecast_hours": 1
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    rain_chance = data['hourly']['precipitation_probability'][0]
    sun_hours = data['daily']['sunshine_duration'][0] / 3600

    return rain_chance, sun_hours

def log_to_influx(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    json_body = [
        {
            "measurement": "device_measurements",
            "tags": {
                "client_id": data["client_id"]
            },
            "fields": {
                "temperature": data["temperature"],
                "humidity": data["humidity"]
            }
        }
    ]
    influxdb_client.write_points(json_body)
        
def logging_thread(): 
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"server_{random.randint(0, 1000)}")
    client.username_pw_set(getenv('MQTT_USERNAME'), getenv("MQTT_PASSWORD"))
    
    client.on_message = log_to_influx

    client.connect(broker_address, broker_port)
    topic_final = f"{topic}/measurements"
    client.subscribe(topic_final)

    print(f"Subscribing to `{topic_final}`. Waiting for messages...")
    client.loop_forever()
    
def decision_thread():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"server_{random.randint(0, 1000)}")
    client.username_pw_set(getenv('MQTT_USERNAME'), getenv("MQTT_PASSWORD"))
    
    client.connect(broker_address, broker_port)
    client.loop_start()

    while True:
        result = influxdb_client.query('SHOW TAG VALUES FROM "devices" WITH KEY = "client_id"')
        client_ids = [entry['value'] for entry in result.get_points()]
        
        result = influxdb_client.query('SELECT * FROM "devices"')
        device_data = list(result.get_points())
        
        for device_id in client_ids:

            # Loop and find the matching device
            for device in device_data:
                if device["client_id"] == device_id:
                    lat = device["lat"]
                    lng = device["lng"]
                    timezone = device["timezone"]
                    break
            
            midnight_utc = datetime.now(timezone_lib.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            
            query = f"""
            SELECT * FROM decisions
            WHERE client_id = '{device_id}'
            AND decision = 1
            AND time >= '{midnight_utc}'
            """
            results = influxdb_client.query(query)

            points = list(results.get_points())
            if len(points) >= 3:
                json_body = [
                    {
                        "measurement": "decisions",
                        "tags": {
                            "client_id": device_id
                        },
                        "fields": {
                            "decision": 0,
                             "reason": "Already watered 3 times."
                        }
                    }
                ]
                
                decision = 0
            else:
                query = f'''
                SELECT * FROM device_measurements
                WHERE "client_id" = '{device_id}'
                ORDER BY time DESC
                LIMIT 1
                '''

                result = influxdb_client.query(query)
                measurements = list(result.get_points())[0]
                
                rain_chance, sun_hours = get_weather_params(lat, lng, timezone)
                
                decision, probability = predict(
                    # Temperature=35,
                    Temperature=measurements["temperature"],
                    Humidity=measurements["humidity"],
                    RainProbability=rain_chance,
                    SunHours=sun_hours
                )
                
                json_body = [
                    {
                        "measurement": "decisions",
                        "tags": {
                            "client_id": device_id
                        },
                        "fields": {
                            "decision": decision,
                            "temperature": measurements["temperature"],
                            "humidity": measurements["humidity"],
                            "rain_chance": rain_chance,
                            "sun_hours": sun_hours
                        }
                    }
                ]
                
            influxdb_client.write_points(json_body)
                
            if(decision):
                payload = json.dumps({
                    "client_id": device_id
                })
                
                topic_final = f"{topic}/decisions"
                print(f"Publishing to {topic_final}")
                client.publish(topic_final, payload, qos=1)
     
        time.sleep(3600)

if __name__ == '__main__':
    thread1 = threading.Thread(target=logging_thread, daemon=True)
    thread2 = threading.Thread(target=decision_thread, daemon=True)

    thread1.start()
    thread2.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Received Ctrl+C. Exiting...")
    
    
