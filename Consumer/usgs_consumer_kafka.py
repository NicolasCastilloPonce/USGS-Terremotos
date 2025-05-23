from confluent_kafka import Consumer, KafkaError
import json
import socket
import time
import boto3
from botocore.exceptions import ClientError

def up_minio():
    return boto3.client(
        's3',
        endpoint_url='http://minio:9000',  # nombre del servicio docker
        aws_access_key_id='minio',
        aws_secret_access_key='minio123',
        region_name='us-east-1'
    )

def save_to_minio(s3:boto3, file_name, data:json):
    bucket_name = "earthquakes"

    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            print("Bucket no existe. Creándolo...")
            s3.create_bucket(Bucket=bucket_name)
        else:
            print("Error inesperado:", e)

    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=json.dumps(data),
        ContentType='application/json'
    )
    print(f"Archivo {file_name} guardado")

def wait_for_kafka(host="kafka", port=9092, timeout=60):
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("✅ Kafka está disponible")
                return
        except OSError:
            if time.time() - start_time > timeout:
                raise TimeoutError("❌ Tiempo de espera agotado para Kafka")
            print("⏳ Esperando a que Kafka esté listo...")
            time.sleep(2)

def have_data(data:json):
    return data["metadata"]["count"] != 0

def get_earthquakes(data:json, s3:boto3):

    url = data["metadata"]["url"]
    index_start = url.index("starttime")
    index_end = url.index("&endtime=")
    file_name = url[index_start+10:index_end]+".json"

    print(f"Mensaje recibido: {file_name}")
    s3 = save_to_minio(s3, file_name, data)

if __name__ == "__main__":
    s3 = up_minio()

    wait_for_kafka()

    c = Consumer({
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'earthquake-consumer-group',
        'auto.offset.reset': 'earliest'
    })

    c.subscribe(['earthquakes'])
    print("Esperando mensajes en el tópico 'earthquakes'...")

    try:
        while True:
            msg = c.poll(1.0)  # espera hasta 1 segundo
            if msg is None:
                continue
            if msg.error():
                print("Error:", msg.error())
            else:
                eq = msg.value().decode('utf-8')
                eq = json.loads(eq)
                print(eq)
                if have_data(eq):
                    get_earthquakes(eq, s3)

    except KeyboardInterrupt:
        pass
    finally:
        c.close()
