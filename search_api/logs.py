import datetime as dt
import logging
import os
import sys
from typing import Literal, Optional, Tuple, Union

from flask import jsonify, request
from flask.wrappers import Response
from flask_log_request_id import current_request_id
from pythonjsonlogger import jsonlogger
from pytz import timezone

IS_LOCAL = os.getenv("IS_LOCAL", None)
STAGE = os.getenv("STAGE", "dev")


class ContextualFilter(logging.Filter):
    def filter(self, log_record):
        log_record.url = request.path
        log_record.method = request.method
        log_record.ip = request.environ.get("REMOTE_ADDR")
        log_record.request_id = current_request_id()
        if STAGE == "test":
            return False
        else:
            return True


def custom_time(*args):
    return dt.datetime.now(timezone("Asia/Tokyo")).timetuple()


json_formatter = jsonlogger.JsonFormatter(
    "%(asctime)s - %(levelname)s - %(message)s - %(lineno)s - %(request_id)d",
    "%Y-%m-%dT%H:%M:%S",
    json_ensure_ascii=False,
)
json_formatter.converter = custom_time
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False

if IS_LOCAL is not None:
    fh = logging.FileHandler("search_api/logs/api.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(json_formatter)
    logger.addHandler(fh)
else:
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(json_formatter)
    logger.addHandler(sh)

request_filter = ContextualFilter()
logger.addFilter(request_filter)
logg_level_4xx = Literal["WARNING", "ERROR"]


class ResponseHandler:
    def __init__(self, message: str = "Function called", extra_message: Optional[dict] = None):
        self.function_called_at: dt.datetime = dt.datetime.now()
        query = request.args.to_dict()
        query = {k: v for k, v in query.items()}
        default_message = {"message": message, "query": query}
        if extra_message is not None:
            logger.info({**default_message, **extra_message})
        else:
            logger.info(default_message)

    def response_4xx(
            self, message: str, status_code: int, log_level: logg_level_4xx = "WARNING"
    ) -> Tuple[Response, int]:
        if status_code < 400 or status_code >= 500:
            raise ValueError
        return_at = dt.datetime.now()
        execution_time = return_at - self.function_called_at
        query = request.args.to_dict()
        query = {k: v for k, v in query.items()}
        log = {
            "message": message,
            "execution_time": execution_time.microseconds / 1000000,
            "query": query,
        }
        if log_level == "WARNING":
            logger.warning(log)
        elif log_level == "ERROR":
            logger.error(log)
        else:
            raise ValueError
        return jsonify({"message": message}), status_code

    def response_2xx(self, data: Union[dict, str, int], status_code: int = 200) -> Tuple[Response, int]:
        if status_code < 200 or status_code >= 300:
            raise ValueError
        return_at = dt.datetime.now()
        execution_time = return_at - self.function_called_at
        logger.info(
            {
                "message": "Successfully executed",
                "execution_time": execution_time.microseconds / 1000000,
                "status": status_code,
            }
        )
        return jsonify(data), status_code
