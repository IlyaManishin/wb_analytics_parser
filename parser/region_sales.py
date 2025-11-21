import time
from datetime import datetime
from typing import List
from pydantic import BaseModel

from . import utils
from . import parsers_config as pconfig

WAIT_TIME = 10


class RegionSale(BaseModel):
    article: int
    seller_article: str
    brand: str
    city_name: str
    region_name: str
    country_name: str
    federal_district: str
    sale_invoice_cost_price: float
    sale_invoice_cost_price_perc: float
    sale_item_invoice_qty: int


def get_region_sales(spreadsheets_id: str, start_date: datetime, end_date: datetime) -> List[RegionSale]:
    token = utils.get_wb_token(spreadsheets_id)
    headers = utils.get_auth_header(token)

    dates_postfix = f'dateFrom={start_date.strftime(r"%Y-%m-%d")}&dateTo={end_date.strftime(r"%Y-%m-%d")}'
    report_url = f"{pconfig.REGION_SALE_URL}?{dates_postfix}"
    result = utils.api_get(report_url, headers, req_wait_sec=WAIT_TIME)
    if not result:
        return []

    time.sleep(WAIT_TIME)
    report = result.get("report", [])
    if not report:
        return []

    article_data_list = utils.get_article_data(spreadsheets_id)
    article_data_map = {
        a.article: a for a in article_data_list} if article_data_list else {}

    stats: List[RegionSale] = []
    for r in report:
        article = r.get("nmID", 0)
        a = article_data_map.get(article)

        stat = RegionSale(
            article=article,
            seller_article=a.seller_article if a else "",
            brand=a.brand if a else "",
            city_name=r.get("cityName", ""),
            region_name=r.get("regionName", ""),
            country_name=r.get("countryName", ""),
            federal_district=r.get("foName", ""),
            sale_invoice_cost_price=r.get("saleInvoiceCostPrice", 0.0),
            sale_invoice_cost_price_perc=r.get(
                "saleInvoiceCostPricePerc", 0.0),
            sale_item_invoice_qty=r.get("saleItemInvoiceQty", 0),
        )
        stats.append(stat)

    return stats
