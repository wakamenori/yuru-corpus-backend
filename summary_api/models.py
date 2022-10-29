import os
from typing import List, TypedDict, Optional

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
    publicationDate: str
    thumbnailUrl: str
    videoUrl: str
    analysed: bool

class NotFoundError(Exception):
    pass


def convert_response_to_summary_data(response: dict) -> SummaryData:
    if "Analysed" not in response.keys():
        analysed = False
    else:
        analysed = response["Analysed"]
    return {
        "id": int(response["Id"]),
        "title": response["Title"],
        "publicationDate": response["PublicationDate"],
        "thumbnailUrl": response["ThumbnailUrl"],
        "videoUrl": response["VideoUrl"],
        "analysed": analysed
    }

class Model:
    def __init__(self):
        db = Database()
        self.corpus_table = db.corpus_table

    def get_all_summary(self) -> List[SummaryData]:
        response = self.corpus_table.query(
            KeyConditionExpression=Key("Type").eq("episode"),
        )
        data = [convert_response_to_summary_data(summary) for summary in response["Items"]]
        return sorted(data, key=lambda x: x["publicationDate"], reverse=False)

    def get_summary_by_episode(self, episode_id: int) -> SummaryData:
        response = self.corpus_table.query(
            KeyConditionExpression=Key("Type").eq("episode") & Key("Id").eq(str(episode_id)),
        )
        if len(response["Items"]) == 0:
            raise NotFoundError("Episode not found")
        summary = response["Items"][0]
        return convert_response_to_summary_data(summary)

