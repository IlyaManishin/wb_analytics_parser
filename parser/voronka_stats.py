import time
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from . import utils
from . import parsers_config as pconfig


class VoronkaStat(BaseModel):
    article: int
    seller_article: str
    brand: str
    stock_count: int
    middle_in_day_sales: float
    turnover_days: Optional[int]
    turnover_hours: Optional[int]
    buyout_percent: float
    orders_count: int
    orders_sum: float
    lost_orders_count: float
    lost_orders_sum: float
    card_opens: Optional[int] = 0
    to_cart: Optional[int] = 0
    ctr: Optional[float] = 0
    buyout_count: int
    buyout_sum: float
    returns_count: int
    returns_sum: float
    deficit_days: Optional[int] = 0


def get_voronka_stats(token: str, start_date: datetime, end_date: datetime) -> List[VoronkaStat]:
    headers = utils.get_auth_header(token)

    stats: List[VoronkaStat] = []
    page = 1
    MAX_PAGES = 30
    WAIT_TIME = 20
    for i in range(MAX_PAGES):
        body = {
            "timezone": "Europe/Moscow",
            "period": {
                "begin": start_date.strftime(r"%Y-%m-%d 00:00:00"),
                "end": end_date.strftime(r"%Y-%m-%d 23:59:00"),
            },
            "orderBy": {
                "field": "ordersSumRub",
                "mode": "asc"
            },
            "page": page
        }

        result = utils.api_post(pconfig.VORONKA_URL,
                                headers, body, req_wait_sec=WAIT_TIME)
        time.sleep(WAIT_TIME)

        data = result.get("data", {})
        cards = data.get("cards", [])
        if not cards:
            break

        for card in cards:
            selected = card.get("statistics", {}).get("selectedPeriod", {})
            stocks = card.get("stocks", {})

            stat = VoronkaStat(
                article=card.get("nmID", 0),
                seller_article=card.get("vendorCode", ""),
                brand=card.get("brandName", ""),
                stock_count=(stocks.get("stocksMp", 0) +
                             stocks.get("stocksWb", 0)),
                middle_in_day_sales=selected.get("avgOrdersCountPerDay", 0.0),
                turnover_days=None,
                turnover_hours=None,
                buyout_percent=selected.get(
                    "conversions", {}).get("buyoutsPercent", 0.0),
                orders_count=selected.get("ordersCount", 0),
                orders_sum=selected.get("ordersSumRub", 0.0),
                lost_orders_count=0,
                lost_orders_sum=0,
                buyout_count=selected.get("buyoutsCount", 0),
                buyout_sum=selected.get("buyoutsSumRub", 0.0),
                returns_count=selected.get("cancelCount", 0),
                returns_sum=selected.get("cancelSumRub", 0.0),
                deficit_days=0,
            )

            stats.append(stat)

        if not data.get("isNextPage"):
            break
        page += 1

    return stats
