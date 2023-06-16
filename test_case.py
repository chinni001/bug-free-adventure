import unittest
from unittest.mock import patch
from lambda_document_iseit_process import parse_sqs_message, lambda_handler


class LambdaHandlerTestcase(unittest.TestCase):

    def test_parse_sqs_message_no_records(self):

        sqs_data = {"Records": []}
        msg_parsed = parse_sqs_message(sqs_data)

        assert msg_parsed == [[], None]


    def test_parse_sqs_message_key_missing_body(self):

        sqs_data = {"Records": [{"receiptHandle": ""}]}
        msg_parsed = parse_sqs_message(sqs_data)
        assert msg_parsed == [[], None]


    def test_parse_sqs_message_key_missing_message(self):

        sqs_data = {"Records": [{"body": "{}"}]}
        msg_parsed = parse_sqs_message(sqs_data)
        assert msg_parsed == [[], None]


    @patch('builtins.print')
    def test_parse_sqs_message_receipt_handle(self, mock_print):

        sqs_data = {
            "Records": [
                {
                    "body": '{"Message": "{}"}',
                    "receiptHandle": "receiptHandle_string"
                },
                {
                    "body": '{"Message": "{}"}',
                    "receiptHandle": "receiptHandle_string_another"
                },            
            ]
        }

        msg_parsed = parse_sqs_message(sqs_data)
        mock_print.assert_called_with("No custom key in message")
        assert msg_parsed == [[], "receiptHandle_string"]


    @patch('builtins.print')
    def test_parse_sqs_message_custom_key_missing(self, mock_print):

        sqs_data = {"Records": [{"body": '{"Message": "{\\"custom\\": \\"{}\\"}"}', "receiptHandle": ""}]}

        msg_parsed = parse_sqs_message(sqs_data)
        mock_print.assert_called_with("No ECSPassThru key in custom")
        assert msg_parsed[0] == []
        

    def test_parse_sqs_message_ecspassthru_data(self):

        sqs_data = {
            "Records": [
                {
                    'body': '{"Message": "{\\"custom\\": \\"{\\\\\\"ECSPassThru\\\\\\": \\\\\\"ecspassthru_value\\\\\\"}\\"}"}',
                    'receiptHandle': 'receiptHandle_string'
                }
            ]
        }

        msg_parsed = parse_sqs_message(sqs_data)
        assert msg_parsed == [["ecspassthru_value"], "receiptHandle_string"]


    @patch('lambda_document_iseit_process.parse_sqs_message')
    @patch('lambda_document_iseit_process.sqs.send_message')
    @patch('lambda_document_iseit_process.sqs.delete_message')
    def test_lambda_handler_success(self, mock_delete_message, mock_send_message, mock_parse_sqs_message):
        event = {
            'Records': [
                {
                    'body': '{"Type": "Notification", "Message": "test_message"}'
                }
            ]
        }
        mock_send_message.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_delete_message.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_parse_sqs_message.return_value = [["ecspass_thru_message"], "receipt_handle"]

        response = lambda_handler(event, None)

        mock_send_message.assert_called_once()
        mock_delete_message.assert_called_once()
        mock_parse_sqs_message.assert_called_once()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], '"Message sent to SQS queue"')


    @patch('lambda_document_iseit_process.parse_sqs_message')
    @patch('lambda_document_iseit_process.sqs.send_message')
    @patch('lambda_document_iseit_process.sqs.delete_message')
    def test_lambda_handler_sqs_failure(self, mock_delete_message, mock_send_message, mock_parse_sqs_message):
        event = {
            'Records': [
                {
                    'body': '{"Type": "Notification", "Message": "test_message"}'
                }
            ]
        }
        mock_send_message.side_effect = Exception("SQS send_message failed")
        mock_delete_message.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_parse_sqs_message.return_value = [["ecspass_thru_message"], "receipt_handle"]

        response = lambda_handler(event, None)

        mock_send_message.assert_called_once()
        mock_delete_message.assert_not_called()
        mock_parse_sqs_message.assert_called_once()

        self.assertEqual(response, 'Failed')


    @patch('lambda_document_iseit_process.parse_sqs_message')
    @patch('lambda_document_iseit_process.sqs.send_message')
    @patch('lambda_document_iseit_process.sqs.delete_message')
    def test_lambda_handler_delete_failure(self, mock_delete_message, mock_send_message, mock_parse_sqs_message):
        event = {
            'Records': [
                {
                    'body': '{"Type": "Notification", "Message": "test_message"}'
                }
            ]
        }
        mock_send_message.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_delete_message.side_effect = Exception("SQS delete_message failed")
        mock_parse_sqs_message.return_value = [["ecspass_thru_message"], "receipt_handle"]

        response = lambda_handler(event, None)

        mock_send_message.assert_called_once()
        mock_delete_message.assert_called_once()
        mock_parse_sqs_message.assert_called_once()

        self.assertEqual(response, 'Failed')


    def test_lambda_handler_missing_records(self):
        event = {}  # Empty event with missing 'Records' key

        response = lambda_handler(event, None)

        self.assertEqual(response, 'Failed')


if _name_ == "_main_":
    unittest.main()
    
    

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


def parse_sqs_message(records):

    sqs_records = []
    receipt_handle = None

    try:
        for record in records["Records"]:
            
            body = json.loads(record["body"])
            message = json.loads(body["Message"])

            if "custom" in message:
                custom_msg = json.loads(message["custom"])
                if "ECSPassThru" in custom_msg:
                    sqs_records.append(custom_msg["ECSPassThru"])
                else:
                    print("No ECSPassThru key in custom")
            else:
                print("No custom key in message")

            if not receipt_handle:
                receipt_handle = record["receiptHandle"]

    except Exception as error:
        print("Exception Occurred", error)

    return [sqs_records, receipt_handle]


def lambda_handler(event, _context):

    # request_id = _context.aws_request_id
    # MessageLogMap.VISCOG001.write_log(LogRequestHeader('', request_id), {})
    # re-invoke sqs in case of lambda failure

    status = "Failed"

    try:
        for record in event["Records"]:

            msg = parse_sqs_message(event)
        
            message = msg[0][0]
            response = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))
            dlt_response = sqs.delete_message(
                QueueUrl="https://sqs.us-east-1.amazonaws.com/976416294762/visioncog-sandbox-doc-mgmt-manifest-iseit",
                ReceiptHandle=msg[1]
            )
            logger.info(f"sent to sqs successfully \'{msg[1]}\'")

        status = {
            "statusCode": 200,
            "body": json.dumps("Message sent to SQS queue")
        }

    except (Exception, ClientError, ValueError, TypeError, KeyError) as error:
        logger.error(f"failed to process the sqs message '{error}'")

    return status


