import json
import os
import re
from typing import List, TypedDict

import boto3
import flask
from flask import Flask, request
from flask_cors import CORS
from flask_log_request_id import RequestID
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from logs import ResponseHandler

app = Flask(__name__)
CORS(app, supports_credentials=True)
RequestID(app)
bp = flask.Blueprint("route", __name__)

STAGE = os.environ.get("STAGE", "dev")

if STAGE == "test":
    STAGE = "dev"

BASE_PATH = os.environ.get("BASE_PATH", "search")


class MatchedItem(TypedDict):
    token: str
    timestamp: str
    speaker: str


class Result(TypedDict):
    episodeId: int
    utterances: List[MatchedItem]


@bp.route("/", methods=["GET"])
def main():
    rh = ResponseHandler()
    search_string = request.args.get("string", None)
    if search_string is None:
        return rh.response_4xx("No search string", 400)
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(f"yuru-corpus-{STAGE}")
    results: List[Result] = []
    for obj in bucket.objects.all():
        matched: List[MatchedItem] = []
        response = obj.get()
        data = response["Body"].read().decode("utf-8")
        json_string = json.loads(data)
        for item in json_string:
            if re.search(search_string, item["Token"]):
                matched.append(
                    {
                        "token": item["Token"],
                        "timestamp": item["Timestamp"],
                        "speaker": item["Speaker"],
                    }
                )
        if len(matched) != 0:
            results.append(
                {"episodeId": int(obj.key.split(".")[0]), "utterances": matched}
            )

    return rh.response_2xx({"result": results}, 200)


@bp.route("/opensearch", methods=["GET"])
def lambda_handler():
    rh = ResponseHandler()
    search_string = request.args.get("string", None)
    if search_string is None:
        return rh.response_4xx("No search string", 400)

    host = "rkoy8np550ngxdqc1u4l.ap-northeast-1.aoss.amazonaws.com"
    region = "ap-northeast-1"
    service = "aoss"
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token,
    )

    client = OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )

    query = {
        "query": {
            "query_string": {"default_field": "Token", "query": f'"{search_string}"'}
        },
        "sort": {"EpisodeId": {"order": "asc"}},
        "size": 1000,
    }
    index_name = f"morphemes-{STAGE}"
    search_response = client.search(body=query, index=index_name)
    hits = search_response["hits"]["hits"]
    results = []

    if len(hits) == 0:
        return rh.response_2xx({"result": []}, 200)

    episode_id = hits[0]["_source"]["EpisodeId"]
    items_in_episode: list[MatchedItem] = []
    for hit in hits:
        item: MatchedItem = {
            "token": hit["_source"]["Token"],
            "timestamp": hit["_source"]["Timestamp"],
            "speaker": hit["_source"]["Speaker"],
        }
        if hit["_source"]["EpisodeId"] == episode_id:
            items_in_episode.append(item)
        else:
            results.append({"episodeId": episode_id, "utterances": items_in_episode})
            episode_id = hit["_source"]["EpisodeId"]
            items_in_episode = [item]

    return rh.response_2xx({"result": results}, 200)


app.register_blueprint(bp, url_prefix=f"/{STAGE}/{BASE_PATH}")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
