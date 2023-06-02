import pytest
from sqs_lambda import parse_sqs_message


def test_parse_sqs_message_no_records():

    sqs_data = {"Records": []}
    msg_parsed = parse_sqs_message(sqs_data)

    assert msg_parsed == [[], None]


@pytest.mark.parametrize("sqs_data, key", [
    ({"Records": [{"receiptHandle": ""}]}, 'body'),
    ({"Records": [{"body": ""}]}, 'Message')
])
def test_parse_sqs_message_key_missing_body(sqs_data, key):

    with pytest.raises(Exception) as exc_info:
        msg_parsed = parse_sqs_message(sqs_data)
        raise KeyError(f"Key '{key}' is missing")

    assert exc_info.value.args[0] == f"Key '{key}' is missing"


@pytest.mark.parametrize("sqs_data, receipt_handle", [
    ({
        "Records": [{
            "body": '{"Message": "{}"}',
            "receiptHandle": "receiptHandle_string"
            }]
    }, "receiptHandle_string"),
    ({
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
    }, "receiptHandle_string"),    
])
def test_parse_sqs_message_receipt_handle(sqs_data, receipt_handle):

    msg_parsed = parse_sqs_message(sqs_data)
    assert msg_parsed == [[], receipt_handle]

@pytest.mark.parametrize("sqs_data", [
    {"Records": [{"body": '{"Message": "{}"}'}]},
    {"Records": [{"body": '{"Message": "{\'custom\': \'\'}"}'}]},
])
def test_parse_sqs_message_custom_key_missing(sqs_data):

    msg_parsed = parse_sqs_message(sqs_data)
    assert msg_parsed[0] == []
    

def test_parse_sqs_message_ecspassthru_data():

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
