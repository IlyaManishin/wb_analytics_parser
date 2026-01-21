import time
from typing import List, Optional
from pydantic import BaseModel

from . import utils
from . import models
from . import parsers_config as pconfig

WAIT_TIME = 20


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



class VoronkaAdvancedStat(BaseModel):
    article: int
    seller_article: str
    brand: str
    category: str
    stock_count: int

    orders_count_1: int
    orders_sum_1: float
    avg_orders_per_day_1: float
    avg_price_1: float
    local_orders_1: int
    buyout_percent_1: float
    buyout_count_1: int
    returns_sum_1: float
    canceled_count_1: int
    delivery_time_days_1: int
    delivery_time_hours_1: int
    delivery_time_mins_1: int
    card_opens_1: int
    to_cart_1: int
    ctr_1: float

    orders_count_2: int
    orders_sum_2: float
    avg_orders_per_day_2: float
    avg_price_2: float
    local_orders_2: int
    buyout_percent_2: float
    buyout_count_2: int
    returns_sum_2: float
    canceled_count_2: int
    delivery_time_days_2: int
    delivery_time_hours_2: int
    delivery_time_mins_2: int
    card_opens_2: int
    to_cart_2: int
    ctr_2: float

    orders_count_diff: float
    orders_sum_diff: float
    buyout_count_diff: float
    buyout_sum_diff: float
    ctr_diff: float


def get_voronka_data(wb_token: str,
                     selected_period: models.WbPeriod, past_period: models.WbPeriod = None) -> list[dict]:
    headers = utils.get_auth_header(wb_token)
    all_cards = []

    MAX_PAGES = 30
    LIMIT = 1000
    offset = 0
    for i in range(MAX_PAGES):
        body = {
            "timezone": "Europe/Moscow",
            "selectedPeriod": selected_period.to_dict(),
            "orderBy": {
                "field": "orderSum",
                "mode": "asc"
            },
            "limit": LIMIT,
            "offset": offset
        }
        if past_period:
            body["pastPeriod"] = past_period.to_dict()

        result = utils.api_post(pconfig.VORONKA_URL,
                                headers, body, req_wait_sec=WAIT_TIME)
        if not result:
            return all_cards
        time.sleep(WAIT_TIME)

        data = result.get("data", {})
        cards = data.get("products", [])
        if not cards:
            break
        all_cards += cards

        if len(cards) < LIMIT:
            break
        offset += LIMIT

    return all_cards


def get_voronka_stats(spreadsheets_id: str, selected: models.WbPeriod) -> List[VoronkaStat]:
    wb_token = utils.get_wb_token(spreadsheets_id)
    stats: List[VoronkaStat] = []
    cards = get_voronka_data(wb_token, selected_period=selected)
    if not cards:
        return []

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

    return stats


def get_advanced_voronka_stats(spreadsheets_id: str, selected: models.WbPeriod, past: models.WbPeriod):
    wb_token = utils.get_wb_token(spreadsheets_id)
    cards = get_voronka_data(wb_token, selected_period=selected)
    if not cards:
        return []

    stats = []
    for card in cards:
        product = card.get("product", {})
        stat = card.get("statistic", {})

        sel = stat.get("selected", {})
        past_stat = stat.get("past", {})

        sel_wb = sel.get("wbClub", {})
        past_wb = past_stat.get("wbClub", {})

        time_sel = sel.get("timeToReady", {})
        time_past = past_stat.get("timeToReady", {})

        open_count_1 = sel.get("openCount", 0)
        open_count_2 = past_stat.get("openCount", 0)
        to_cart_1 = sel.get("cartCount", 0)
        to_cart_2 = past_stat.get("cartCount", 0)

        ctr_1 = (to_cart_1 / open_count_1) if open_count_1 else 0
        ctr_2 = (to_cart_2 / open_count_2) if open_count_2 else 0

        stat_obj = VoronkaAdvancedStat(
            article=product.get("nmId", 0),
            seller_article=product.get("vendorCode", ""),
            brand=product.get("brandName", ""),
            category=product.get("subjectName", ""),
            stock_count=product.get("stocks", {}).get("mp", 0) + product.get("stocks", {}).get("wb", 0),

            orders_count_1=sel.get("orderCount", 0),
            orders_sum_1=sel.get("orderSum", 0.0),
            avg_orders_per_day_1=sel.get("avgOrdersCountPerDay", 0.0),
            avg_price_1=sel.get("avgPrice", 0.0),
            local_orders_1=sel_wb.get("orderCount", 0),
            buyout_percent_1=sel_wb.get("buyoutPercent", 0.0),
            buyout_count_1=sel.get("buyoutCount", 0),
            returns_sum_1=sel.get("cancelSum", 0.0),
            canceled_count_1=sel.get("cancelCount", 0),
            delivery_time_days_1=time_sel.get("days", 0),
            delivery_time_hours_1=time_sel.get("hours", 0),
            delivery_time_mins_1=time_sel.get("mins", 0),
            card_opens_1=open_count_1,
            to_cart_1=to_cart_1,
            ctr_1=ctr_1,

            orders_count_2=past_stat.get("orderCount", 0),
            orders_sum_2=past_stat.get("orderSum", 0.0),
            avg_orders_per_day_2=past_stat.get("avgOrdersCountPerDay", 0.0),
            avg_price_2=past_stat.get("avgPrice", 0.0),
            local_orders_2=past_wb.get("orderCount", 0),
            buyout_percent_2=past_wb.get("buyoutPercent", 0.0),
            buyout_count_2=past_stat.get("buyoutCount", 0),
            returns_sum_2=past_stat.get("cancelSum", 0.0),
            canceled_count_2=past_stat.get("cancelCount", 0),
            delivery_time_days_2=time_past.get("days", 0),
            delivery_time_hours_2=time_past.get("hours", 0),
            delivery_time_mins_2=time_past.get("mins", 0),
            card_opens_2=open_count_2,
            to_cart_2=to_cart_2,
            ctr_2=ctr_2,

            orders_count_diff=sel.get("orderCount", 0) - past_stat.get("orderCount", 0),
            orders_sum_diff=sel.get("orderSum", 0.0) - past_stat.get("orderSum", 0.0),
            buyout_count_diff=sel.get("buyoutCount", 0) - past_stat.get("buyoutCount", 0),
            buyout_sum_diff=sel.get("buyoutSum", 0.0) - past_stat.get("buyoutSum", 0.0),
            ctr_diff=ctr_1 - ctr_2
        )
        stats.append(stat_obj)

    return stats