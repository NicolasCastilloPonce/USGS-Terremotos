import requests
from datetime import datetime as dt, UTC, timedelta
from time import sleep, time
from confluent_kafka import Producer
import json
import socket

seconds_to_sleep = 20

def import_earthquakes(starttime = "2025-05-13T02:20:07", endtime = ""):
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={starttime}&endtime={endtime}"
    data = {}

    try:
        response = requests.get(url)

        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ocurrió un error al realizar la solicitud: {e}")

    return data

def wait_for_kafka(host="kafka", port=9092, timeout=60):
    start_time = time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("✅ Kafka está disponible")
                return
        except OSError:
            if time() - start_time > timeout:
                raise TimeoutError("❌ Tiempo de espera agotado para Kafka")
            print("⏳ Esperando a que Kafka esté listo...")
            sleep(2)

def get_time_utc():

    seconds_to_substract = seconds_to_sleep
    time_diff = timedelta(seconds = seconds_to_substract, minutes=5)

    date_time_now_utc = dt.now(UTC)
    date_time_now_utc_seconds_to_past = date_time_now_utc - time_diff

    final_datetime = date_time_now_utc_seconds_to_past.strftime("%Y-%m-%dT%H:%M:%S")
    return f"{final_datetime}"

def delivery_report(err, msg):
    if err is not None:
        print(f"Error al enviar: {err}")
    else:
        print(f"Evento enviado a {msg.topic()} [{msg.partition()}]")

def topic_kafka(quake_data:json, producer = Producer({'bootstrap.servers': 'kafka:9092'}) ):
    producer.produce("earthquakes", quake_data.encode("utf-8"), callback=delivery_report)
    producer.flush()

if __name__ == "__main__":
    #print(get_time_utc())
    wait_for_kafka()
    while(True):
       eq = import_earthquakes(starttime = get_time_utc())
       eq = json.dumps(eq)
       topic_kafka(quake_data = eq)
       sleep(seconds_to_sleep)
