import os
from typing import List, TypedDict

import boto3
from boto3.dynamodb.conditions import Key

STAGE = os.getenv("STAGE", "dev")
is_local = os.getenv("IS_LOCAL", None)


class Database:
    def __init__(self):
        if is_local is not None:
            db = boto3.resource(
                "dynamodb",
                endpoint_url="http://dynamodb-local:8000",
                region_name="ap-northeast-1",
            )
        else:
            db = boto3.resource(
                "dynamodb",
                region_name="ap-northeast-1",
            )
        if STAGE == "dev":
            self.corpus_table = db.Table(f"YuruCorpusDev")
        elif STAGE == "prod":
            self.corpus_table = db.Table(f"YuruCorpusProd")
        elif STAGE == "test":
            self.corpus_table = db.Table(f"YuruCorpusTest")
        else:
            raise ValueError("Invalid environment")


class MorphemeData(TypedDict):
    timestamp: str
    token: str


class NotFoundError(Exception):
    pass


class Model:
    def __init__(self):
        db = Database()
        self.corpus_table = db.corpus_table

    def get_morpheme(self, episode_id) -> List[MorphemeData]:
        response = self.corpus_table.query(
            KeyConditionExpression=Key("Type").eq("morpheme") & Key("Id").begins_with(str(episode_id) + "#"),
        )
        if len(response["Items"]) == 0:
            raise NotFoundError("Morpheme not found")
        data = [{
            "timestamp": morpheme["Id"].split("#")[1],
            "token": morpheme["Token"],
        } for morpheme in response["Items"]]
        return sorted(data, key=lambda x: x["timestamp"], reverse=False)
