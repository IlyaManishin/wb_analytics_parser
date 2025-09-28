import requests
import time
import json

from .parser_config import *
from .parser_exceptions import *

def get_auth_header(token: str) -> dict:
    header = {"Authorization": token}
    return header


def api_get(url: str, headers: dict, attempts: int) -> list[dict] | dict:
    resp = None
    for i in range(attempts):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_WAIT_SEC)
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