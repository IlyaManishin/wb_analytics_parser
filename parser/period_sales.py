import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

from .data import models
from . import parser_config as config
from . import utils
from . import parser_exceptions as exc

@dataclass
class RawSalesEntry:
    article: int
    date: datetime
    warehouseName: str
    supplierArticle: str
    subject: str
    brand: str
    finishedPrice: int
    

def get_month_sales(token: str) -> list[RawSalesEntry]:
    now = datetime.now()
    header = utils.get_auth_header(token)
    url_time = (now - timedelta(days=config.SALES_PERIOD_DAYS)).strftime(r"%Y-%m-%d")
    url = f"https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom={url_time}"

    resp = utils.api_get(url, header, config.REQUEST_ATTEMPT_COUNT)
    res = []
    for i in resp:
        if "nmId" not in i:
            continue
        entry = RawSalesEntry(
            article=i.get("nmId", 0),
            date=datetime.strptime(i.get("date", "1970-01-01T00:00:00"), "%Y-%m-%dT%H:%M:%S").date(),
            warehouseName=i.get("warehouseName", ""),
            supplierArticle=i.get("supplierArticle", ""),
            subject=i.get("subject", ""),
            brand=i.get("brand", ""),
            finishedPrice=i.get("finishedPrice", 0),
        )
        res.append(entry)
    return res

def extract_period_sales(raw_data: list[RawSalesEntry]) -> list[models.SalesEntry]:
    pass


def parse_period_sales(token: str) -> list[models.SalesEntry]:
    now = datetime.now()
    try:
        resp = get_month_sales(token)
        if not resp:
            logging.error("No data in period sales")
            return []        
    except Exception as err:
        logging.error(err)
        return []
    
    
    

