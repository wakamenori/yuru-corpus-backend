import os
from typing import List, Literal, Optional, TypedDict
import json

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

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


class MorphemeResponse(TypedDict):
    timestamp: str
    token: str
    speaker: str


class NotFoundError(Exception):
    status_code = 404


class AlreadyExistsError(Exception):
    status_code = 403


class MorphemeData(TypedDict):
    Type: Literal["Morpheme"]
    Id: str
    Token: str
    Speaker: str


class MorphemeRequest(TypedDict):
    timestamp: str
    speaker: str
    token: str


class Model:
    def __init__(self):
        db = Database()
        self.corpus_table = db.corpus_table

    def _is_morpheme_exist(self, episode_id, timestamp):
        response = self.corpus_table.query(
            KeyConditionExpression=Key("Type").eq("Morpheme") & Key("Id").eq(f"{episode_id}#{timestamp}#0"),
        )
        return len(response["Items"]) != 0

    def _update_item(self, episode_id: int, data: MorphemeRequest):
        items: MorphemeData = {
            "Type": "Morpheme",
            "Id": f"{episode_id}#{data['timestamp']}#0",
            "Token": data["token"],
            "Speaker": data["speaker"]
        }
        response = self.corpus_table.put_item(Item=items)
        return response

    def _sync_json_with_db(self, episode_id: int):
        """sync json file in s3 bucket"""
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(f"yuru-corpus-{STAGE}")
        obj = bucket.Object(f"{episode_id}.json")
        data = self.corpus_table.query(
            KeyConditionExpression=Key("Type").eq("Morpheme") & Key("Id").begins_with(f"{episode_id}#"),
        )["Items"]
        data = [{"Token": item["Token"], "Speaker": item["Speaker"], "Timestamp": item["Id"].split("#")[1]} for item in data]
        obj.put(Body=json.dumps(data))

    def get_morpheme(self, episode_id, timestamp: Optional[str] = None) -> List[MorphemeResponse]:
        if timestamp is None:
            response = self.corpus_table.query(
                KeyConditionExpression=Key("Type").eq("Morpheme") & Key("Id").begins_with(str(episode_id) + "#"),
            )
            if len(response["Items"]) == 0:
                raise NotFoundError("Morpheme not found")
            data = [{
                "timestamp": morpheme["Id"].split("#")[1],
                "token": morpheme["Token"],
                "speaker": morpheme["Speaker"],
            } for morpheme in response["Items"]]
            return sorted(data, key=lambda x: x["timestamp"], reverse=False)
        else:
            response = self.corpus_table.query(
                KeyConditionExpression=Key("Type").eq("Morpheme") & Key("Id").eq(f"{episode_id}#{timestamp}#0"),
            )
            if len(response["Items"]) == 0:
                raise NotFoundError("Morpheme not found")
            data = {
                "timestamp": response["Items"][0]["Id"].split("#")[1],
                "token": response["Items"][0]["Token"],
                "speaker": response["Items"][0]["Speaker"],
            }
            return [data]

    def post_morpheme(self, episode_id: int, data: MorphemeRequest):
        if self._is_morpheme_exist(episode_id, data["timestamp"]):
            raise AlreadyExistsError("Morpheme already exists")
        response = self._update_item(episode_id, data)
        self._sync_json_with_db(episode_id)
        return response

    def put_morpheme(self, episode_id: int, data: MorphemeRequest):
        if not self._is_morpheme_exist(episode_id, data["timestamp"]):
            raise NotFoundError("Morpheme not found")
        response = self._update_item(episode_id, data)
        self._sync_json_with_db(episode_id)
        return response

    def delete_morpheme(self, episode_id: int, timestamp: str):
        try:
            response = self.corpus_table.delete_item(
                Key={
                    "Type": "Morpheme",
                    "Id": f"{episode_id}#{timestamp}#0",
                },
                ConditionExpression="attribute_exists(#PK) AND attribute_exists(Id)",
                ExpressionAttributeNames={"#PK": "Type"},
            )
            self._sync_json_with_db(episode_id)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise NotFoundError("Morpheme not found")
