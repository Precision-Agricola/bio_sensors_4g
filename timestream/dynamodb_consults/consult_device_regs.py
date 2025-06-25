"""Read Dynamo registers"""

import boto3
from boto3.dynamodb.conditions import Key
from pprint import pprint
from wasabi import Printer

msg = Printer()


device_owner = {
    "owner": "Caleb de la Vara",
    "device_id": "ESP32_5EABBC",
    "sever_id": "SERVER_3D6F30"
}

dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1'
)

table = dynamodb.Table('bioiot_sensors_v1.3')
device_id = 'ESP32_5EABBC'
limit = 10

response = table.query(
    KeyConditionExpression=Key('device_id').eq(device_id),
    ScanIndexForward=False,
    Limit=limit
)

if not response['Items']:
    msg.fail(f"Owner: {device_owner['owner']} has no devices id data")
else:
    msg.good(f"Owner: {device_owner['owner']} has registered data")

for item in response['Items']:
    print("\n --- Registros ---")
    pprint(item)


