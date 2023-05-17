import boto3

def lambda_handler(event, context):
    # Create SQS clients
    sqs_source = boto3.client('sqs')
    sqs_destination = boto3.client('sqs')

    # Define the source and destination SQS queue URLs
    source_queue_url = 'your-source-queue-url'
    destination_queue_url = 'your-destination-queue-url'

    # Receive messages from the source SQS queue
    response = sqs_source.receive_message(
        QueueUrl=source_queue_url,
        MaxNumberOfMessages=10,  # Maximum number of messages to receive (adjust as needed)
        AttributeNames=['All'],
        MessageAttributeNames=['All'],
        WaitTimeSeconds=20  # Wait up to 20 seconds for messages (adjust as needed)
    )

    # Process received messages
    if 'Messages' in response:
        for message in response['Messages']:
            # Extract message attributes and body
            message_attributes = message['MessageAttributes']
            message_body = message['Body']

            # Send the message to the destination SQS queue
            sqs_destination.send_message(
                QueueUrl=destination_queue_url,
                MessageBody=message_body,
                MessageAttributes=message_attributes
            )

            # Delete processed message from the source SQS queue
            sqs_source.delete_message(
                QueueUrl=source_queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
    else:
        print('No messages in the source queue.')
