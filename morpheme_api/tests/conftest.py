import sys
from typing import List, TypedDict

import pytest
from api import app
from models import Model

sys.path.append("../")


class Morpheme(TypedDict):
    Type: str
    Id: str
    Speaker: str
    Token: str


data: List[Morpheme] = [
    {
        "Type": "Morpheme",
        "Id": "1#00:00:01#0",
        "Speaker": "AA",
        "Token": "token 1"
    }, {
        "Type": "Morpheme",
        "Id": "1#00:00:02#0",
        "Speaker": "BB",
        "Token": "token 2"
    },
]


def init_db():
    db = Model()
    response = db.corpus_table.scan()
    all_items = response["Items"]
    for item in all_items:
        if item["Type"] == "Morpheme":
            db.corpus_table.delete_item(
                Key={
                    "Type": "Morpheme",
                    "Id": item["Id"],
                },
                ConditionExpression="attribute_exists(#PK) AND attribute_exists(Id)",
                ExpressionAttributeNames={"#PK": "Type"},
            )
    for item in data:
        db.corpus_table.put_item(Item=item)


@pytest.fixture
def client(scope="function"):
    init_db()
    with app.test_client() as client:
        with app.app_context():
            yield client
