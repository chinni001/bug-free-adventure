import boto3
import time


def lambda_handler(event, context):
    for record in event['Records']:
        print("Received a new message from SQS. Processing it")
        payload = record["body"]
        print(str(payload))
        write_to_dynamoDB(str(payload))

        
def write_to_dynamoDB(data):
    # Create a DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    
    # Specify the name of the table
    table_name = 'SQS_DataStore'
    
    # Get a handle on the table
    table = dynamodb.Table(table_name)
    
    # Create an item to insert
    item = {
        'ID': str(round(time.time() * 1000)),  # This gets the current timestamp in milliseconds
        'data': data
    }
    
    # Insert the item into the table
    response = table.put_item(Item=item)
    
    # Print the response
    print(response)
