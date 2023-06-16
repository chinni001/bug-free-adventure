import os
import json
import time
import boto3
import logging
import datetime
from botocore.exceptions import ClientError
# from log_util import LogRequestHeader, MessageLogMap

log_format = "%(message)s"
logging.basicConfig(format=log_format)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

queue_url = os.environ.get('DOC_MQ_SQS_URL')
fire_table_name = os.environ.get('FIRE_EMAIL_DYNAMO_NAME')


def parse_sqs_message(sqs_records):

    rec_dict = {}

    try:
        record = sqs_records[0]

        body = json.loads(record['body'])
        message = json.loads(body['Message'])

        if 'custom' in message:
            custom = json.loads(message['custom'])
            if 'ECSPassThru' in custom:
                rec_dict["ecspass_thru"] = custom['ECSPassThru']

        rec_dict["receipt_handle"] = record["receiptHandle"]

        return rec_dict

    except (json.decoder.JSONDecodeError, Exception) as error:
        logger.exception(f"Failed to parse the message {error}")


def lambda_handler(event, _context):

    # request_id = _context.aws_request_id
    # MessageLogMap.VISCOG001.write_log(LogRequestHeader('', request_id), {})
    # re-invoke sqs in case of lambda failure
    
    sqs_msg_dict = parse_sqs_message(event['Records'])

    if not sqs_msg_dict.get("ecspass_thru"):
        return {
            "message": "SQS Messages not found"
        }

    try:
        response = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(sqs_msg_dict["ecspass_thru"]))
        dlt_response = sqs.delete_message(
            QueueUrl="https://sqs.us-east-1.amazonaws.com/976416294762/visioncog-sandbox-doc-mgmt-manifest-iseit",
            ReceiptHandle=sqs_msg_dict["receipt_handle"]
        )
        logger.info(f"sent to sqs successfully \'{sqs_msg_dict['ecspass_thru']}\'")

        return {
            "status": 200,
            "message": "SQS Message processed successfully"
        }

    except (ClientError, Exception) as error:
        logger.error(f"failed to process the sqs message '{error}'")

        return "Failed"
