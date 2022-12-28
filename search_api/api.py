import json
import os
import re
from typing import TypedDict, List

import flask
from flask import Flask, request
from flask_cors import CORS
from flask_log_request_id import RequestID
import boto3
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
                {"episodeId": obj.key.split(".")[0], "utterances": matched}
            )

    return rh.response_2xx({"result": results}, 200)


app.register_blueprint(bp, url_prefix=f"/{STAGE}/{BASE_PATH}")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
