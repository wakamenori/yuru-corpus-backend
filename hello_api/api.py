import os

import flask
from flask import Flask, request
from flask_cors import CORS
from flask_log_request_id import RequestID

from logs import ResponseHandler

app = Flask(__name__)
CORS(app, supports_credentials=True)
RequestID(app)
bp = flask.Blueprint("route", __name__)

STAGE = os.environ.get("STAGE", "dev")
BASE_PATH = os.environ.get("BASE_PATH", "hello")  # TODO: change base path


@bp.route("/", methods=["GET", "POST"])
def main():
    if request.method == "GET":
        rh = ResponseHandler()
        return rh.response_2xx(f"Hello, World!!! stage:{STAGE}")
    if request.method == "POST":
        rh = ResponseHandler()
        data = request.get_json()
        return rh.response_2xx(data, 201)


@bp.route("/hello/", methods=["GET", "POST"])
def hello():
    if request.method == "GET":
        rh = ResponseHandler()
        return rh.response_2xx(f"Hello!, Hello World! stage:{STAGE}")
    if request.method == "POST":
        rh = ResponseHandler()
        data = request.get_json()
        return rh.response_2xx(data, 201)


app.register_blueprint(bp, url_prefix=f"/{STAGE}/{BASE_PATH}")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
