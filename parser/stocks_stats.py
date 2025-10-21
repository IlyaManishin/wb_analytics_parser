import time
from typing import List, Dict
from pydantic import BaseModel

from . import utils
from . import parsers_config as pconfig


class RegionStat(BaseModel):
    region_name: str
    stock_percent: float


class CityStat(BaseModel):
    region_name: str
    city_name: str
    stock_count: int


class StockStat(BaseModel):
    article: int
    seller_article: str
    brand: str
    category: str
    all_stocks: int
    region_stats: List[RegionStat]
    city_stats: List[CityStat]


def get_stocks_stub():
    """Заглушка для метода получения остатков товаров"""
    return [
        {
            "brand": "Wonderful",
            "subjectName": "Фотоальбомы",
            "vendorCode": "41058/прозрачный",
            "nmId": 183804172,
            "warehouses": [
                {"warehouseName": "Невинномысск", "quantity": 134},
                {"warehouseName": "Коледино", "quantity": 133},
                {"warehouseName": "В пути до получателей", "quantity": 14},
            ],
        },
        {
            "brand": "Neuro",
            "subjectName": "Блокноты",
            "vendorCode": "AB-2025",
            "nmId": 193456789,
            "warehouses": [
                {"warehouseName": "Коледино", "quantity": 72},
                {"warehouseName": "Казань", "quantity": 48},
            ],
        },
    ]


def get_warehouse_map(token: str) -> Dict[str, Dict[str, str]]:
    headers = utils.get_auth_header(token)
    offices = utils.api_get(pconfig.OFFICES_URL, headers)
    if not offices:
        return []

    warehouse_map: Dict[str, Dict[str, str]] = {}
    for off in offices:
        name = off.get("name")
        if not name:
            continue
        region = off.get("federalDistrict") or "Остальные"
        city = off.get("city") or "Неизвестно"
        warehouse_map[name] = {"region": region, "city": city}


def get_stock_stats() -> List[StockStat]:
    token = utils.get_wb_token()
    warehouse_map = get_warehouse_map(token)

    stocks_data = get_stocks_stub()
    if not stocks_data:
        return []

    stats: List[StockStat] = []

    for item in stocks_data:
        article = item.get("nmId", 0)
        seller_article = item.get("vendorCode", "")
        brand = item.get("brand", "")
        category = item.get("subjectName", "")
        warehouses = item.get("warehouses", [])

        if not warehouses:
            continue

        total_stocks = sum(w.get("quantity", 0) for w in warehouses)
        if total_stocks == 0:
            continue

        region_stocks: Dict[str, int] = {}
        city_stocks: Dict[str, int] = {}

        for wh in warehouses:
            wh_name = wh.get("warehouseName")
            qty = wh.get("quantity", 0)
            if not wh_name or qty <= 0:
                continue

            wh_info = warehouse_map.get(
                wh_name, {"region": "Остальные", "city": wh_name})
            region = wh_info["region"]
            city = wh_info["city"]

            region_stocks[region] = region_stocks.get(region, 0) + qty
            city_stocks[city] = city_stocks.get(city, 0) + qty

        region_stats = [
            RegionStat(region_name=r, stock_percent=round(
                q / total_stocks * 100, 2))
            for r, q in region_stocks.items()
        ]

        city_stats = [
            CityStat(region_name=warehouse_map.get(next((w["warehouseName"] for w in warehouses if warehouse_map.get(w["warehouseName"], {}).get("city") == c), ""), {}).get("region", "Остальные"),
                     city_name=c,
                     stock_count=q)
            for c, q in city_stocks.items()
        ]

        stat = StockStat(
            article=article,
            seller_article=seller_article,
            brand=brand,
            category=category,
            all_stocks=total_stocks,
            region_stats=region_stats,
            city_stats=city_stats,
        )
        stats.append(stat)

    return stats
