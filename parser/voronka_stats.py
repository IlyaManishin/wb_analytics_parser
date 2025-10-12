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
    # deficit_days: Optional[int] = 0


def get_voronka_stats(start_date: datetime, end_date: datetime) -> List[VoronkaStat]:
    token = utils.get_wb_token()
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
        if not result:
            return
        time.sleep(WAIT_TIME)

        data = result.get("data", {})
        cards = data.get("cards", [])
        if not cards:
            break

        for card in cards:
            sel = card.get("statistics", {}).get("selectedPeriod", {})
            stocks = card.get("stocks", {})

            stat = VoronkaStat(
                article=card.get("nmID", 0),
                seller_article=card.get("vendorCode", ""),
                brand=card.get("brandName", ""),
                stock_count=stocks.get("stocksMp", 0) +
                stocks.get("stocksWb", 0),
                middle_in_day_sales=sel.get("avgOrdersCountPerDay", 0.0),
                buyout_percent=sel.get("conversions", {}).get(
                    "buyoutsPercent", 0.0),
                orders_count=sel.get("ordersCount", 0),
                orders_sum=sel.get("ordersSumRub", 0.0),
                lost_orders_count=sel.get("cancelCount", 0.0),
                lost_orders_sum=sel.get("cancelSumRub", 0.0),
                card_opens=sel.get("openCardCount", 0),
                to_cart=sel.get("addToCartCount", 0),
                ctr=(sel.get("addToCartCount", 0) / sel.get("openCardCount", 1)
                     if sel.get("openCardCount") else 0),
                buyout_count=sel.get("buyoutsCount", 0),
                buyout_sum=sel.get("buyoutsSumRub", 0.0),
                returns_count=sel.get("cancelCount", 0),
                returns_sum=sel.get("cancelSumRub", 0.0),
                # deficit_days=sel.get("officeMissingTime", {}).get("days", 0)
            )

            stats.append(stat)

        if not data.get("isNextPage"):
            break
        page += 1

    return stats
