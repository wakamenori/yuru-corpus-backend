import sys

sys.path.append("../")

import sys
from typing import List, TypedDict

import pytest
from api import app
from models import Model

sys.path.append("../")


class SummaryData(TypedDict):
    Type: str
    Id: str
    Title: str
    PublicationDate: str
    ThumbnailUrl: str
    VideoUrl: str
    IsAnalyzed: bool
    Channel: str


data: List[SummaryData] = [
    {
        "Type": "Morpheme",
        "Id": "1",
        "Title": "「イルカも喋る」は大ウソ【言語学って何？】#1",
        "PublicationDate": "2021-01-11",
        "ThumbnailUrl": "https://i.ytimg.com/vi/2YY9DT4uDh0/sddefault.jpg",
        "VideoUrl": "https://www.youtube.com/watch?v=2YY9DT4uDh0",
        "IsAnalyzed": True,
        "Channel": "ゆる言語学ラジオ",
    },
    {
        "Type": "Morpheme",
        "Id": "2",
        "Title": "test",
        "PublicationDate": "2021-01-01",
        "ThumbnailUrl": "test",
        "VideoUrl": "test",
        "IsAnalyzed": True,
        "Channel": "test",
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
    with app.test_client() as client:
        with app.app_context():
            yield client
