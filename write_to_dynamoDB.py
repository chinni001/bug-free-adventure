import boto3

# Create a DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='your-region-name')

# Specify the name of the table
table_name = 'your-table-name'

# Get a handle on the table
table = dynamodb.Table(table_name)

# Create an item to insert
item = {
    'id': '12345',
    'name': 'Sample Data'
}

# Insert the item into the table
response = table.put_item(Item=item)

# Print the response
print(response)
