import json
from datetime import datetime
import boto3
import botocore
from io import BytesIO
from PIL import Image, ImageOps
import os
import uuid
import json
import logging


s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION'))
dynamodb_resource = boto3.resource(
    'dynamodb', region_name=os.environ.get('AWS_REGION'))
thumbnail_size = int(os.environ.get('THUMBNAIL_SIZE'))
thumbnail_folder = os.environ.get("THUMBNAIL_FOLDER")
dynamodb_table = os.environ.get("DYNAMODB_TABLE")
images_table = dynamodb_resource.Table(dynamodb_table)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info(f"Loading function ....")


def get_image_from_s3(bucket, key):

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_content = response['Body'].read()

        file = BytesIO(image_content)
        image = Image.open(file)
    except botocore.exceptions.ClientError as error:
        logger.error(f"get_image_from_s3 :: Error - {error}")
        raise error
    except botocore.exceptions.ParamValidationError as error:
        logger.error(f"get_image_from_s3 :: Error - {error}")
        raise ValueError(f"The parameters you provided are incorrect: {error}")
    
    return image


def generate_thumbnail(image):
    try:
        return ImageOps.fit(image, (thumbnail_size, thumbnail_size), Image.ANTIALIAS)
    except Exception as error:
        logger.error(f"generate_thumbnail :: Error - {error}")
        raise error



def get_event_type(event_name):
    try:
        event_split = event_name.rsplit(':', 1)
        return event_split[0]
    except Exception as error:
        logger.error(f"get_event_type :: Error - {error}")
        raise error


def generate_thumbnail_name(key):

    try:
        key_split = key.rsplit('.', 1)
        return key_split[0] + "_thumbnail.png"
    except Exception as error:
        logger.error(f"generate_thumbnail_name :: Error - {error}")
        raise error



def save_thumbnail_metadata_to_dynamodb(bucket_name, original_image_key, original_image_size, thumbnail_url, thumbnail_size):

    try:
        response = images_table.get_item(
            Key={
                'originalImageURI': f"s3://{bucket_name}/{original_image_key}"
            }
        )
    except botocore.exceptions.ClientError as error:
        logger.error(f"save_thumbnail_metadata_to_dynamodb :: Error - {error}")
        raise error
    except botocore.exceptions.ParamValidationError as error:
        logger.error(f"save_thumbnail_metadata_to_dynamodb :: Error - {error}")
        raise ValueError(f"The parameters you provided are incorrect: {error}")


    if response.keys() in ["Item"]:
        created_at = response["Item"]["createdAt"]
    else:
        created_at = str(datetime.now())

    try:
        response = images_table.put_item(
            Item={
                'originalImageURI': f"s3://{bucket_name}/{original_image_key}",
                'thumbnailURL': thumbnail_url,
                'originalImageSize': original_image_size,
                'thumbnailImageSize': thumbnail_size,
                'createdAt': created_at,
                'updatedAt': str(datetime.now())
            }
        )
    except botocore.exceptions.ClientError as error:
        logger.error(f"save_thumbnail_metadata_to_dynamodb :: Error - {error}")
        raise error
    except botocore.exceptions.ParamValidationError as error:
        logger.error(f"save_thumbnail_metadata_to_dynamodb :: Error - {error}")
        raise ValueError(f"The parameters you provided are incorrect: {error}")

    return {
        "statusCode":200,
        "message": "Item inserted into the table successfully!"
    }



def delete_thumbnail_metadata_from_dynamo(bucket_name, original_image_key):

    try:
        response = images_table.delete_item(
            Key={
                "originalImageURI": f"s3://{bucket_name}/{original_image_key}"
            }
        )
        logger.info(
            f"Item deleted from images metadata DynamoDB table.")
    except botocore.exceptions.ClientError as error:
        logger.error(f"delete_thumbnail_metadata_from_dynamo :: Error - {error}")
        raise error
    except botocore.exceptions.ParamValidationError as error:
        logger.error(f"delete_thumbnail_metadata_from_dynamo :: Error - {error}")
        raise ValueError(f"The parameters you provided are incorrect: {error}")

def upload_thumbnail_to_s3(bucket_name, original_image_key, original_image_size, thumbnail_name, thumbnail_image):
    # We're saving the image into a BytesIO object to avoid writing to disk
    out_thumbnail = BytesIO()  # old way- no longer supported fp.StringIO()

    # You MUST specify the file type because there is no file name to discern
    # it from
    thumbnail_image.save(out_thumbnail, 'PNG')
    thumbnail_size = out_thumbnail.__sizeof__()

    out_thumbnail.seek(0)
    logger.info(f"bucket name: {bucket_name}")
    logger.info(f"original image key : {original_image_key.split('/')[-1]}")
    logger.info(f"thumbnail name : {thumbnail_name}")
    logger.info(f"original image size : {original_image_size}")

    response = s3_client.put_object(
        # ACL='public-read',
        Body=out_thumbnail,
        Bucket=bucket_name,
        ContentType='image/png',
        Key=f"{thumbnail_folder}/{thumbnail_name.split('/')[-1]}"
    )

    thumbnail_url = f"{s3_client.meta.endpoint_url}/{bucket_name}/{thumbnail_folder}/{thumbnail_name.split('/')[-1]}"

    # save image url to db
    save_thumbnail_metadata_to_dynamodb(
        bucket_name, original_image_key, original_image_size, thumbnail_url, thumbnail_size)

    return thumbnail_url


def delete_thumbnail_from_s3(bucket_name, original_image_key, thumbnail_image_key):
    logger.info(f"Bucket: {bucket_name}")
    logger.info(f"Original image key: {original_image_key}")
    logger.info(f"Thumbnail image key: {thumbnail_image_key}")

    delete_thumbnail_metadata_from_dynamo(bucket_name, original_image_key)

    logger.info(f"original image key : {original_image_key}")
    logger.info(f"thumbnail image key : {thumbnail_image_key}")
    response = s3_client.delete_object(
        Bucket=bucket_name,
        Key=thumbnail_image_key
    )
    logger.info(f"delete_thumbnail_from_s3 response = {json.dumps(response)}")

    return {
        "statusCode": 200,
        "body": "Thumbnail removed from S3 bucket"

    }


def s3_thumbnail_generator(event, context):
    # Parse event
    event_name = event['Records'][0]['eventName']
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    original_image_key = event['Records'][0]['s3']['object']['key']

    logger.info(f"bucket name :: {bucket_name}")
    logger.info(f"original image key :: {original_image_key}")

    if get_event_type(event_name) == "ObjectCreated":
        original_image_size = event['Records'][0]['s3']['object']['size']
        logger.info(f"object_size :: {original_image_size}")
        logger.info("Object Created :: s3://{bucket_name}{original_image_key}")

        if (original_image_key.split(".")[0]).endswith('_thumbnail') == False:
            original_image = get_image_from_s3(bucket_name, original_image_key)
            thumbnail_image = generate_thumbnail(original_image)
            thumbnail_name = generate_thumbnail_name(original_image_key)
            thumbnail_url = upload_thumbnail_to_s3(
                bucket_name, original_image_key, original_image_size, thumbnail_name, thumbnail_image)
            body = {
                "thumbnail_url": thumbnail_url,
                "input": event,
            }

            return {"statusCode": 200,
                    "body": json.dumps(body)
                    }
        else:
            return {
                "statusCode": 400,
                "body": {
                    "message": "Cannot generate a thumbnail of an already thumbnail image",
                    "input": json.dumps(event)
                }
            }
    elif get_event_type(event_name) == "ObjectRemoved":
        thumbnail_name = (generate_thumbnail_name(
            original_image_key)).split("/")[-1]
        response = delete_thumbnail_from_s3(
            bucket_name, original_image_key, f"{thumbnail_folder}/{thumbnail_name}")
        return response

def s3_get_thumbnail_urls(event, context):
    # get all image urls from the db and show in a json format
    response = images_table.scan()
    logger.info(response)
    data = []
    for item in response["Items"]:
        data.append(dict(originalImageURI=item["originalImageURI"],thumbnailURL=item["thumbnailURL"]))

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(data)
    }