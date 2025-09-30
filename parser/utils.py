import requests
import time
import json
from enum import Enum
from typing import Union

from .parser_config import *
from .parser_exceptions import *


class RequestTypes(Enum):
    GET = "GET"
    POST = "POST"


def get_auth_header(token: str) -> dict:
    header = {"Authorization": token}
    return header


def _send_request(url: str, headers: dict, attempts: int, mode: RequestTypes, body: dict = None) -> Union[list[dict], dict]:
    resp = None
    for i in range(attempts):
        try:
            if mode == RequestTypes.GET:
                resp = requests.get(url, headers=headers,
                                    timeout=REQUEST_WAIT_SEC)
            elif mode == RequestTypes.POST:
                if body is None:
                    body = {}
                resp = requests.post(url, headers=headers,
                                     json=body, timeout=REQUEST_WAIT_SEC)
            if resp.status_code == 401:
                raise UnathorizedExc()
            if resp.status_code != 200:
                raise Exception

            data = json.loads(resp.text)
            return data
        except UnathorizedExc as err:
            raise
        except Exception as err:
            time.sleep(REQUEST_WAIT_SEC)

    raise InvalidRequestExc(url, resp.text if resp else "")


def api_get(url: str, headers: dict, attempts: int = REQUEST_ATTEMPT_COUNT) -> Union[list[dict], dict]:
    return _send_request(url, headers, attempts, RequestTypes.GET)


def api_post(url: str, headers: dict, body: dict, attempts: int = REQUEST_ATTEMPT_COUNT) -> Union[list[dict], dict]:
    return _send_request(url, headers, attempts, RequestTypes.POST, body)
