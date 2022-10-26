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


class SummaryData(TypedDict):
    id: int
    title: str
    publication_date: str
    thumbnail_url: str
    video_url: str


class Model:
    def __init__(self):
        db = Database()
        self.corpus_table = db.corpus_table

    def get_all_summary(self) -> List[SummaryData]:
        response = self.corpus_table.query(
            KeyConditionExpression=Key("Type").eq("episode"),
        )
        data = [{
            "id": int(summary["Id"]),
            "title": summary["Title"],
            "publication_date": summary["PublicationDate"],
            "thumbnail_url": summary["ThumbnailUrl"],
            "video_url": summary["VideoUrl"],
        } for summary in response["Items"]]
        return sorted(data, key=lambda x: x["publication_date"], reverse=False)
