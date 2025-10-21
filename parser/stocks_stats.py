import time
from typing import List, Dict
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

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


def get_stocks_report() -> Optional[Dict[str, Any]]:
    token = utils.get_wb_token()
    if not token:
        logging.error("Can't get token")
        return None

    headers = utils.get_auth_header(token)
    group_by = "groupByNm=true&groupByBrand=true&groupBySubject=true&groupBySa=true&groupBySize=true"
    create_report_url = f"{pconfig.WB_WAREHOUSE_REMAINS_URL}?{group_by}"
    create_resp = utils.api_get(create_report_url, headers)
    task_id = create_resp.get("data", {}).get("taskId")
    if not task_id:
        logging.error("Can't get warehouse task")
        return None

    status_url = pconfig.WB_WAREHOUSE_STATUS_URL.format(task_id=task_id)
    bad_statuses = {"purged", "canceled"}

    for _ in range(pconfig.WB_STATUS_ATTEMPTS):
        status_resp = utils.api_get(status_url, headers)
        status = status_resp.get("data", {}).get("status")
        if not status or status in bad_statuses:
            logging.error("Invalid status from warehouses report")
            return None
        if status == "done":
            break
        time.sleep(5)
    else:
        return None

    download_url = pconfig.WB_WAREHOUSE_DOWNLOAD_URL.format(task_id=task_id)
    report_data = utils.api_get(download_url, headers)
    return report_data


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

    stocks_data = get_stocks_report()
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
