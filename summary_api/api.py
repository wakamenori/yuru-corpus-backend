import os

import flask
from flask import Flask
from flask_cors import CORS
from flask_log_request_id import RequestID

from logs import ResponseHandler
from models import Model, NotFoundError

app = Flask(__name__)
CORS(app, supports_credentials=True)
RequestID(app)
bp = flask.Blueprint("route", __name__)

STAGE = os.environ.get("STAGE", "dev")
if STAGE == "test":
    STAGE = "dev"

BASE_PATH = os.environ.get("BASE_PATH", "summary")


@bp.route("/", methods=["GET"])
def main():
    rh = ResponseHandler()
    db = Model()
    summary = db.get_all_summary()
    return rh.response_2xx({"summary": summary})


@bp.route("/by_episode/<int:episode_id>/", methods=["GET"])
def get_summary_by_episode(episode_id):
    rh = ResponseHandler()
    db = Model()
    try:
        summary = db.get_summary_by_episode(episode_id)
    except NotFoundError as e:
        return rh.response_4xx(str(e), 404)
    return rh.response_2xx(summary)


app.register_blueprint(bp, url_prefix=f"/{STAGE}/{BASE_PATH}")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
