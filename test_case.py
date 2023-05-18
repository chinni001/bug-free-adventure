import boto3
import pytest

# Set up SQS clients
sqs_source = boto3.client('sqs')
sqs_destination = boto3.client('sqs')

# Set up test queue URLs
source_queue_url = 'your-source-queue-url'
destination_queue_url = 'your-destination-queue-url'

def test_single_message_transfer():
    # Send a single message to the source queue
    message_body = 'Test message'
    sqs_source.send_message(QueueUrl=source_queue_url, MessageBody=message_body)

    # Invoke the function to read and transfer the message
    read_messages_from_queue(source_queue_url, destination_queue_url)

    # Retrieve the messages from the destination queue
    response = sqs_destination.receive_message(QueueUrl=destination_queue_url, MaxNumberOfMessages=1)

    # Verify that the message is received correctly in the destination queue
    assert 'Messages' in response
    assert response['Messages'][0]['Body'] == message_body

def test_multiple_message_transfer():
    # Send multiple messages to the source queue
    messages = ['Message 1', 'Message 2', 'Message 3']
    for message in messages:
        sqs_source.send_message(QueueUrl=source_queue_url, MessageBody=message)

    # Invoke the function to read and transfer the messages
    read_messages_from_queue(source_queue_url, destination_queue_url)

    # Retrieve the messages from the destination queue
    response = sqs_destination.receive_message(QueueUrl=destination_queue_url, MaxNumberOfMessages=len(messages))

    # Verify that all messages are received correctly in the destination queue
    assert 'Messages' in response
    received_messages = [msg['Body'] for msg in response['Messages']]
    assert received_messages == messages

# Run the tests
pytest.main()
