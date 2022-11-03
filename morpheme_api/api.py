import json
import os
import re

import flask
from flask import Flask, request
from flask_cors import CORS
from flask_log_request_id import RequestID
from jsonschema import FormatChecker, validate
from jsonschema.exceptions import ValidationError

from logs import ResponseHandler
from models import AlreadyExistsError, Model, NotFoundError

app = Flask(__name__)
CORS(app, supports_credentials=True)
RequestID(app)
bp = flask.Blueprint("route", __name__)

STAGE = os.environ.get("STAGE", "dev")

if STAGE == "test":
    STAGE = "dev"

BASE_PATH = os.environ.get("BASE_PATH", "morpheme")


def validate_request(request_body, file_name: str):
    base = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.normpath(os.path.join(base, f"schemas/{file_name}"))
    with open(json_path, "r", encoding="utf-8") as file:
        schema = json.load(file)
    validate(request_body, schema, format_checker=FormatChecker())


@bp.route("/by_episode/<int:episode_id>/", methods=["GET", "POST", "PUT", "DELETE"])
def main(episode_id):
    rh = ResponseHandler()
    if request.method == "GET":
        try:
            db = Model()
            timestamp = request.args.get("timestamp", None)
            if timestamp is not None:
                matched = re.match(r"^([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$", timestamp)
                if matched is None:
                    return rh.response_4xx(f"Invalid timestamp: {timestamp}", 400)
            morphemes = db.get_morpheme(episode_id, timestamp)
            return rh.response_2xx({"morphemes": morphemes})
        except NotFoundError as e:
            return rh.response_4xx(str(e), e.status_code)

    if request.method == "POST":
        data = request.get_json()
        try:
            validate_request(data, "update_morpheme.json", )
            db = Model()
            db.post_morpheme(episode_id, data)
            return rh.response_2xx({"message": "Morpheme created"}, 201)
        except AlreadyExistsError as e:
            return rh.response_4xx(str(e), e.status_code)
        except ValidationError as e:
            return rh.response_4xx(f"Invalid request body. {e.message}", 400)

    if request.method == "PUT":
        data = request.get_json()
        try:
            validate_request(data, "update_morpheme.json", )
            db = Model()
            db.put_morpheme(episode_id, data)
            return rh.response_2xx({"message": "Morpheme updated"}, 201)
        except NotFoundError as e:
            return rh.response_4xx(str(e), e.status_code)
        except ValidationError as e:
            return rh.response_4xx(f"Invalid request body. {e.message}", 400)

    if request.method == "DELETE":
        timestamp = request.args.get("timestamp")
        try:
            db = Model()
            db.delete_morpheme(episode_id, timestamp)
            return rh.response_2xx({"message": "Morpheme deleted"}, 202)
        except NotFoundError as e:
            return rh.response_4xx(str(e), e.status_code)


app.register_blueprint(bp, url_prefix=f"/{STAGE}/{BASE_PATH}")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
