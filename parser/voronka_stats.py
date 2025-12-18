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
    category: str
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


def get_voronka_stats(spreadsheets_id: str, start_date: datetime, end_date: datetime) -> List[VoronkaStat]:
    token = utils.get_wb_token(spreadsheets_id)
    headers = utils.get_auth_header(token)

    stats: List[VoronkaStat] = []

    MAX_PAGES = 30
    LIMIT = 1000
    WAIT_TIME = 20
    offset = 0
    for i in range(MAX_PAGES):
        body = {
            "timezone": "Europe/Moscow",
            "selectedPeriod": {
                "start": start_date.strftime(r"%Y-%m-%d"),
                "end": end_date.strftime(r"%Y-%m-%d"),
            },
            "orderBy": {
                "field": "orderSum",
                "mode": "asc"
            },
            "limit" : LIMIT,
            "offset" : offset
        }

        result = utils.api_post(pconfig.VORONKA_URL,
                                headers, body, req_wait_sec=WAIT_TIME)
        if not result:
            return stats
        time.sleep(WAIT_TIME)
        
        data = result.get("data", {})
        cards = data.get("products", [])
        if not cards:
            break

        for card in cards:
            product = card.get("product", {})
            stat = card.get("statistic", {})
            sel = stat.get("selected", {})
            conv = sel.get("conversions", {})
            stocks = product.get("stocks", {})

            open_count = sel.get("openCount", 0)
            cart_count = sel.get("cartCount", 0)

            stat_obj = VoronkaStat(
                article=product.get("nmId", 0),
                seller_article=product.get("vendorCode", ""),
                brand=product.get("brandName", ""),
                category=product.get("subjectName", ""),
                stock_count=stocks.get("mp", 0) + stocks.get("wb", 0),
                middle_in_day_sales=sel.get("avgOrdersCountPerDay", 0.0),
                buyout_percent=conv.get("buyoutPercent", 0.0),
                orders_count=sel.get("orderCount", 0),
                orders_sum=sel.get("orderSum", 0.0),
                lost_orders_count=sel.get("cancelCount", 0),
                lost_orders_sum=sel.get("cancelSum", 0.0),
                card_opens=open_count,
                to_cart=cart_count,
                ctr=(cart_count / open_count) if open_count else 0,
                buyout_count=sel.get("buyoutCount", 0),
                buyout_sum=sel.get("buyoutSum", 0.0),
                returns_count=sel.get("cancelCount", 0),
                returns_sum=sel.get("cancelSum", 0.0),
            )

            stats.append(stat_obj)

        if len(cards) < LIMIT:
            break
        offset += LIMIT

    return stats
