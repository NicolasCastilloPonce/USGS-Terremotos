from prefect import flow, task, get_run_logger
import boto3
from botocore.exceptions import ClientError

@task
def up_minio():
    return boto3.client(
        's3',
        endpoint_url='http://minio:9000',  # nombre del servicio docker
        aws_access_key_id='minio',
        aws_secret_access_key='minio123',
        region_name='us-east-1'
    )

@task
def get_earthquakes_from_minio(s3:boto3, bucket="earthquakes"):
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            print("Bucket no existe")
        else:
            print("Error inesperado:", e)


    return s3.get_object(
            Bucket = bucket
        )
@task
def get_list_objects(s3:boto3, bucket = "earthquakes"):
    files = s3.list_objects_v2(
            Bucket = bucket
        )

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

    #earthquakes = get_earthquakes_from_minio(s3)
    #print(earthquakes)
    #logger.info("Se extraen los archivos de S3")

if __name__ == '__main__':

    upload_earthqaukes()
