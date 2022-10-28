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

BASE_PATH = os.environ.get("BASE_PATH", "morpheme")


@bp.route("/by_episode/<int:episode_id>/", methods=["GET"])
def main(episode_id):
    rh = ResponseHandler()
    try:
        db = Model()
        morphemes = db.get_morpheme(episode_id)
        return rh.response_2xx({"morphemes": morphemes})
    except NotFoundError as e:
        return rh.response_4xx(str(e), 404)


app.register_blueprint(bp, url_prefix=f"/{STAGE}/{BASE_PATH}")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
