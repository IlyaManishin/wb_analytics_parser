import logging
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from pydantic import BaseModel
import json

from . import parser_config as pconfig
from .parser_config import service
from . import utils
from . import parser_exceptions as exc


class DayStats(BaseModel):
    sales_count: int
    difference: int


class SalesStat(BaseModel):
    article: int
    seller_article: str
    brand: str
    month_sales: int
    middle_in_day_sales: int
    period_income: int
    no_available_days: int

    days_stats: list[DayStats]


class Sale(BaseModel):
    article: int
    date: date


def init_sales_entry(article: int, warehouseName: str, supplierArticle: str, subject: str, brand: str) -> SalesStat:
    entry = SalesStat(article=article,
                      brand=brand,
                      middle_in_day_sales=0, period_income=0, no_available_days=0,
                      days_stats=[])
    for i in range(pconfig.SALES_PERIOD_DAYS + 1):
        entry.days_stats.append(DayStats(sales_count=0, difference=0))
    return entry


def init_empty_sales_entry(article: int):
    return init_sales_entry(article, "", "", "", "")


def get_period_stats(token: str, articles: list[int], start: datetime, end: datetime) -> list[dict]:
    all_items = []
    limit = 1000

    for i in range(0, len(articles), limit):
        batch = articles[i:i + limit]

        body = {
            "nmIDs": batch,
            "currentPeriod": {
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d")
            },
            "stockType": "",
            "skipDeletedNm": True,
            "orderBy": {
                "field": "ordersCount",
                "mode": "asc"
            },
            "availabilityFilters": [
                "deficient",
                "actual",
                "balanced",
                "nonActual",
                "nonLiquid",
                "invalidData",
            ],
            "limit": limit,
            "offset": 0
        }

        headers = utils.get_auth_header(token)
        result = utils.api_post(pconfig.SALES_STATS_URL, headers, body)

        items = result.get("data", {}).get("items", [])
        if not items:
            break
        all_items += items
        if len(items) < limit:
            break

    return all_items


def get_period_sales(token: str, start_date: datetime) -> list[Sale]:
    header = utils.get_auth_header(token)
    url_time = start_date.strftime(r"%Y-%m-%d")
    url = f"{pconfig.SALES_URL}?dateFrom={url_time}"

    resp = utils.api_get(url, header, 5)
    if not resp:
        return
    res = []
    for i in resp:
        if "nmId" not in i:
            continue
        entry = Sale(
            article=i.get("nmId", 0),
            date=datetime.strptime(
                i.get("date", "1970-01-01T00:00:00"), r"%Y-%m-%dT%H:%M:%S").date(),
        )
        res.append(entry)
    return res


def get_sales_stats(token, articles: list[int]) -> list[SalesStat]:
    now = datetime.now()

    end_date = now - timedelta(days=1)
    start_date = end_date - timedelta(days=pconfig.SALES_PERIOD_DAYS - 1)

    month_stats = get_period_stats(
        token, articles, end_date - timedelta(days=30), end_date)
    month_sales = get_period_sales(token, start_date)
    if not month_stats or not month_sales:
        return None

    date_range = [(start_date + timedelta(days=d)).date()
                  for d in range(pconfig.SALES_PERIOD_DAYS + 1)]

    sales_by_article_date = {a: {d: 0 for d in date_range} for a in articles}

    for sale in month_sales:
        if sale.article in sales_by_article_date and sale.date in sales_by_article_date[sale.article]:
            sales_by_article_date[sale.article][sale.date] += 1

    sales_stats = []
    month_stats_dict = {item.get("nmID"): item for item in month_stats}

    for article_id in articles:
        item = month_stats_dict.get(article_id, {})
        seller_article = item.get("vendorCode", "")
        brand = item.get("brandName", "")
        metrics = item.get("metrics", {})

        article_sales = sales_by_article_date.get(article_id, {})
        sorted_dates = sorted(article_sales.keys())
        not_available = metrics.get("officeMissingTime", {}).get("days", 0)

        days_stats = []
        total_sales = 0

        for i in range(1, len(sorted_dates)):
            day_date = sorted_dates[i]
            prev_date = sorted_dates[i - 1]

            sales_count = article_sales[day_date]
            prev_sales = article_sales[prev_date]
            difference = sales_count - prev_sales

            total_sales += sales_count
            days_stats.append(
                DayStats(sales_count=sales_count, difference=difference))

        sales_stat = SalesStat(
            article=str(article_id),
            seller_article=seller_article,
            brand=brand,
            month_sales=sum(article_sales.values()),
            middle_in_day_sales=int(total_sales / max(len(days_stats), 1)),
            period_income=metrics.get("ordersSum", 0),
            no_available_days=not_available,
            days_stats=days_stats
        )

        sales_stats.append(sales_stat)
    return sales_stats


def convert_sales_stats_to_table(articles: list[int], stats: list[SalesStat]) -> list[list]:
    base_columns = ["Артикул WB", "Артикул поставщика", "Бренд", "Всего продаж за месяц",
                    "Среднее количество заказов в день", "Выручка за 7 дней (руб)", "Товара нет в наличии (дней)"]
    data = []
    data.append(["", "Дата обновления:",
                datetime.now().strftime(r"%Y-%m-%d %H:%M")])
    header_up = [""] * len(base_columns)
    for i in range(pconfig.DIFF_DAYS_COUNT, 0, -1):
        header_up += [f"{i} д. назад"] * 2
    data.append(header_up)

    header_down = []
    header_down += base_columns
    for i in range(pconfig.DIFF_DAYS_COUNT):
        header_down += ["Заказы", "Динамика"]
    data.append(header_down)
    
    article_res = {}
    for i in stats:
        article_res[i.article] = i

    for article in articles:
        if article not in article_res:
            data.append([])
        else:
            row = []
            stat: SalesStat = article_res[article]

            row.append(stat.article)
            row.append(stat.seller_article)
            row.append(stat.brand)
            row.append(stat.month_sales)
            row.append(stat.middle_in_day_sales)
            row.append(stat.period_income)
            row.append(stat.no_available_days)

            for day_stat in stat.days_stats:
                row.append(day_stat.sales_count)
                row.append(day_stat.difference)
            data.append(row)
    return data

def save_sales_stats_to_sheet(data: list[list]):
    spreadsheet_id = pconfig.table_id
    sheet_name = pconfig.SALES_STATS_SHEET_NAME
    range_name = f"{pconfig.SALES_STATS_SHEET_NAME}!A:ZZ"
    body = {
        "values": data
    }

    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=sheet_name
    ).execute()

    tryings = 3
    for _ in range(tryings):
        try:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body
            ).execute()
            break
        except:
            pass


def period_sales_task():
    articles = utils.get_profitability_articles()
    if not articles:
        logging.error("No profitability articles")
    token = utils.get_wb_token()
    if not token:
        logging.error("No wb token")

    stats = get_sales_stats(token, articles)
    if not stats:
        logging.error("Can't get stats")
    google_data = convert_sales_stats_to_table(articles, stats)
    save_sales_stats_to_sheet(google_data)
    # with open("res.json", "w", encoding="utf-8") as file:
    #     dump_data = [i.model_dump() for i in res]
    #     file.write(json.dumps(dump_data, ensure_ascii=False))
