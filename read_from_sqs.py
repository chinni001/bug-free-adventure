import boto3

# Create an SQS client
sqs = boto3.client('sqs', region_name='your-region-name')

# Specify the URL of the queue
queue_url = 'your-queue-url'

# Receive messages from the queue
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=10,
    VisibilityTimeout=30,
    WaitTimeSeconds=20
)

# Loop through the messages
for message in response.get('Messages', []):
    # Get the message body
    message_body = message['Body']
    
    # Print the message body
    print('Received message: {}'.format(message_body))
    
    # Delete the message from the queue
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=message['ReceiptHandle']
    )
