import pytest
from tests.fixtures.moto import dynamodb

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
