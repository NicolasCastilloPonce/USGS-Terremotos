from prefect import flow, task, get_run_logger
import boto3
from botocore.exceptions import ClientError
import json

@task
def up_minio():
    return boto3.client(
        's3',
        endpoint_url='http://minio:9000',  # nombre del servicio docker
        aws_access_key_id='minio',
        aws_secret_access_key='minio123',
        region_name='us-east-1'
    )

def exists_bucket(s3:boto3, bucket="earthquakes"):
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            print("Bucket no existe")
        else:
            print("Error inesperado:", e)

@task
def get_list_objects(s3:boto3, bucket = "earthquakes"):
    exists_bucket(s3)
    files = s3.list_objects_v2(
            Bucket = bucket
        )

    return files

@task
def get_earthquakes_from_minio(s3:boto3, list_files, bucket="earthquakes"):
    exists_bucket(s3)

    files = []
    for f in list_files["Contents"]:
        s3_file = s3.get_object(
            Bucket = bucket,
            Key = f["Key"]
        )

        body = s3_file["Body"].read()

        data = json.loads(body.decode('utf-8'))
        files.append(data)

    return files

@task
def read_earthquakes():
    return null

@flow
def upload_earthqaukes():
    logger = get_run_logger()

    s3 = up_minio()
    logger.info("Se levanta bucket S3")

    earthquakes_list = get_list_objects(s3)
    logger.info(earthquakes_list)
    logger.info("Se rescata el listado de objetos en bucket")

    earthquakes = get_earthquakes_from_minio(s3, earthquakes_list)
    logger.info(earthquakes)
    logger.info(f"Se extraen los archivos de S3. Cantidad de elementos: {len(earthquakes)}")

if __name__ == '__main__':

    upload_earthqaukes()
