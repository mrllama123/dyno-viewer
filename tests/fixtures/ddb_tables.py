import random
import uuid
import pytest
from tests.fixtures.moto import dynamodb
from decimal import Decimal as D


def create_ddb_table(dynamodb, name, gsi_count=0):
    AttributeDefinitions = [
        {"AttributeName": "pk", "AttributeType": "S"},
        {"AttributeName": "sk", "AttributeType": "S"},
    ]

    for i in range(gsi_count):
        AttributeDefinitions.append(
            {"AttributeName": f"gsipk{i + 1}", "AttributeType": "S"}
        )
        AttributeDefinitions.append(
            {"AttributeName": f"gsisk{i + 1}", "AttributeType": "S"}
        )

    GlobalSecondaryIndexes = [
        {
            "IndexName": f"gsi{i + 1}Index",
            "KeySchema": [
                {"AttributeName": f"gsipk{i + 1}", "KeyType": "HASH"},
                {"AttributeName": f"gsisk{i + 1}", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
        }
        for i in range(gsi_count)
    ]

    props = dict(
        TableName=name,
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},  # Partition key
            {"AttributeName": "sk", "KeyType": "RANGE"},  # Sort key
        ],
        AttributeDefinitions=AttributeDefinitions,
        ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
    )

    if gsi_count:
        props.setdefault("GlobalSecondaryIndexes", GlobalSecondaryIndexes)

    return dynamodb.create_table(**props)


@pytest.fixture
def ddb_tables(dynamodb):
    return [
        create_ddb_table(dynamodb, table_name, 2)
        for table_name in [
            "dawnstar",
            "falkreath",
            "markarth",
            "morthal",
            "raven",
            "riften",
            "solitude",
            "whiterun",
            "windhelm",
            "winterhold",
        ]
    ]


@pytest.fixture
def ddb_test_data():
    return [
        {
            "pk": "customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d",
            "sk": "CUSOMER",
            "gsipk1": "CUSTOMER",
            "gsisk1": "customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d",
            "test": "test1",
        },
        {
            "pk": "customer#455b3e2e-8c81-4405-b402-0f4b94221265",
            "sk": "CUSOMER",
            "test": "test1",
        },
        {
            "pk": "customer#97b297a7-b21c-4efc-b8c4-bfcbe54cd5f7",
            "sk": "CUSOMER",
            "test": "test1",
        },
        {
            "pk": "customer#d374bf00-78af-4912-97a6-d5e2bda01c4a",
            "sk": "CUSOMER",
            "test": "test1",
        },
        {
            "pk": "customer#4907bd44-283b-4e74-b4c4-06941dc9425e",
            "sk": "CUSOMER",
            "test": "test1",
        },
        {
            "pk": "customer#8c5b486c-b4ef-4391-b1b9-ab0088a57cd7",
            "sk": "CUSOMER",
            "test": "test1",
        },
        {
            "pk": "customer#ca658612-7c16-4d86-b4d1-a7e1db572782",
            "sk": "CUSOMER",
            "test": "test1",
        },
        {
            "pk": "customer#89f7f080-db5a-47ee-87b5-55f742552103",
            "sk": "CUSOMER",
            "test": "test1",
        },
        {
            "pk": "customer#b6ccc161-6e76-44b7-96cc-5ff36fcff16a",
            "sk": "CUSOMER",
            "test": "test1",
        },
        {
            "pk": "customer#df7ebf28-b556-433f-b3a2-a396dd624aab",
            "sk": "CUSOMER",
            "test": "test1",
        },
        {
            "pk": "1234567890",
            "sk": "JohnDoe",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "123-456-7890",
        },
        {
            "pk": "9876543210",
            "sk": "JaneDoe",
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "phone": "456-789-0123",
        },
        *[
            {
                "pk": "1234567890",
                "sk": f"Order{index}",
                "orderId": str(uuid.uuid4()),
                "orderDate": f"2023-{random.randint(1,12)}-{random.randint(1, 30)}",
                "totalAmount": round(D(random.uniform(1, 10000)), 2),
            }
            for index in range(1, 100)
        ],
        *[
            {
                "pk": "9876543210",
                "sk": f"Order{index}",
                "orderId": str(uuid.uuid4()),
                "orderDate": f"2023-{random.randint(1,12)}-{random.randint(1, 30)}",
                "totalAmount": round(D(random.uniform(1, 10000)), 2),
            }
            for index in range(1, 100)
        ],
    ]


@pytest.fixture
def ddb_table(ddb_tables):
    return ddb_tables[0]


@pytest.fixture
def ddb_table_with_data(ddb_table, ddb_test_data):
    for item in ddb_test_data:
        ddb_table.put_item(Item=item)

    return ddb_test_data
