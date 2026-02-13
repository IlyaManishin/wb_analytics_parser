import requests
import time
import json
from enum import Enum
from typing import Union
import logging
from pydantic import BaseModel
import os

from .parsers_config import *
from .parser_exceptions import *


class RequestTypes(Enum):
    GET = "GET"
    POST = "POST"


class ArticleData(BaseModel):
    article: int
    seller_article: str
    brand: str
    category: str


def get_auth_header(token: str) -> dict:
    header = {"Authorization": token}
    return header


def _send_request(url: str,
                  headers: dict,
                  attempts: int,
                  on_error_wait_sec: int,
                  mode: RequestTypes,
                  body: dict = None) -> Union[list[dict], dict]:
    resp = None
    for i in range(attempts):
        try:
            if mode == RequestTypes.GET:
                resp = requests.get(url, headers=headers,
                                    timeout=on_error_wait_sec)
            elif mode == RequestTypes.POST:
                if body is None:
                    body = {}
                resp = requests.post(url, headers=headers,
                                     json=body, timeout=on_error_wait_sec)
            if resp.status_code != 200:
                logging.error(
                    f"Api error (status={resp.status_code}) resp = {resp.text}, url = {url}")
            if resp.status_code == 401:
                raise UnathorizedExc()
            if resp.status_code != 200:
                raise Exception(f"Request error, status: {resp.status_code}")

            data = json.loads(resp.text)
            return data
        except UnathorizedExc as err:
            raise
        except Exception as err:
            if resp and resp.status_code == 429:
                time.sleep(on_error_wait_sec)
                continue
            logging.exception(err)
    logging.error(
        f"Invalid request: url={url}" + f", status={resp.status_code}" if resp else "")
    return None


def api_get(url: str, headers: dict,
            attempts: int = REQUEST_ATTEMPT_COUNT,
            req_wait_sec=REQUEST_WAIT_SEC) -> Union[list[dict], dict]:
    return _send_request(url, headers, attempts, req_wait_sec, RequestTypes.GET)


def api_post(url: str, headers: dict, body: dict,
             attempts: int = REQUEST_ATTEMPT_COUNT,
             req_wait_sec=REQUEST_WAIT_SEC) -> Union[list[dict], dict]:
    return _send_request(url, headers, attempts, req_wait_sec, RequestTypes.POST, body)


def read_google_table(spreadsheets_id, name, table_range) -> list[list[str]]:
    tryings = 3
    values = None
    for i in range(tryings):
        try:
            values = service.spreadsheets().values().get(spreadsheetId=spreadsheets_id,
                                                         range=f"{name}!{table_range}").execute()["values"]
            break
        except Exception as err:
            logging.exception(err)
            continue
    if not values:
        return []
    return values

def write_entries_to_google(spreadsheet_id: str, range_: str, data: list[dict], attempts=3):
    if len(data) == 0:
        return
    
    headers = list(data[0].keys())
    values = [headers] + [list(entry.values()) for entry in data]

    body = {
        "values": values
    }
    for i in range(attempts):
        try:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueInputOption="RAW",
                body=body
            ).execute()
            break
        except Exception as err:
            logging.exception(err)
            time.sleep(5)


def get_article_data(table_id: str) -> list[ArticleData]:
    data = read_google_table(table_id, PROFITABILITY_SHEET_NAME,
                      PROFITABILITY_ARTICLES_RANGE)
    if not data:
        return None
    res = []
    try:
        for row in data:
            if len(row) < 4:
                continue
            article = int(row[0])
            seller_article = row[1]
            brand = row[2]
            category = row[3]
            res.append(ArticleData(
                article=article,
                seller_article=seller_article,
                brand=brand,
                category=category))
    except:
        pass
    return res


def get_wb_token(table_id: str) -> str:
    data = read_google_table(table_id, TOKEN_SHEET_NAME, TOKEN_RANGE)
    if not data:
        return None
    try:
        return data[0][0].strip("\n, ")
    except:
        return None


def get_spreadsheets_ids():
    ids_path = os.path.join(PARSER_DIR, "security_settings",
                            "voronka_spreadsheets_id.txt")
    with open(ids_path, 'r', encoding='utf-8') as file:
        content = file.read().strip()
        if not content:
            return []
        ids = [id.strip() for id in content.split(',') if id.strip()]
        return ids
