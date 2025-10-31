import logging
from datetime import datetime, timedelta, date
from pydantic import BaseModel
import time
from dataclasses import dataclass

from . import parsers_config as pconfig
from .parsers_config import service
from . import utils
from .data import db


@dataclass
class _RunConfig:
    DIFF_DAYS_COUNT: int
    IS_DEBUG: bool


class DayStats(BaseModel):
    sales_count: int
    stocks_count: int


class SalesStat(BaseModel):
    article: int
    seller_article: str
    brand: str
    category: str
    month_sales: int
    cur_stocks: int
    middle_in_day_sales: float
    month_income: int
    no_available_days: int

    days_stats: list[DayStats]

    saleRate: int
    availability: str


class Sale(BaseModel):
    article: int
    date: date


def get_period_stats(token: str, articles: list[int], start: datetime, end: datetime) -> list[dict]:
    all_items = []
    limit = 1000

    for i in range(0, len(articles), limit):
        batch = articles[i:i + limit]

        body = {
            "nmIDs": batch,
            "currentPeriod": {
                "start": start.strftime(r"%Y-%m-%d"),
                "end": end.strftime(r"%Y-%m-%d")
            },
            "stockType": "",
            "skipDeletedNm": True,
            "orderBy": {
                "field": "ordersCount",
                "mode": "asc"
            },
            "availabilityFilters": [
                # "deficient",
                # "actual",
                # "balanced",
                # "nonActual",
                # "nonLiquid",
                # "invalidData",
            ],
            "limit": limit,
            "offset": 0
        }

        headers = utils.get_auth_header(token)
        result = utils.api_post(pconfig.SALES_STATS_URL,
                                headers, body, req_wait_sec=20)
        time.sleep(20)

        items = result.get("data", {}).get("items", [])
        if not items:
            break
        all_items += items

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


def read_sales_stats(token, config: _RunConfig,  articles_data: list[utils.ArticleData]) -> list[SalesStat]:
    articles = [i.article for i in articles_data]
    now = datetime.now()

    end_date = now - timedelta(days=1)
    start_date = end_date - timedelta(days=config.DIFF_DAYS_COUNT - 1)

    month_stats = get_period_stats(token, articles, start_date, end_date)
    if not month_stats:
        return None

    today_stocks: dict[int, int] = {}
    month_data = {}
    for item in month_stats:
        article = item["nmID"]
        metrics = item.get("metrics", {})

        month_sales = metrics.get("ordersCount", 0)
        avg_sales = metrics.get("avgOrders", 0)
        period_income = metrics.get("ordersSum", 0)
        not_available = metrics.get("officeMissingTime", {}).get("days", 30)

        stocks = metrics.get("stockCount", 0)
        today_stocks[article] = stocks

        month_data[article] = dict(
            month_sales=month_sales,
            middle_in_day_sales=avg_sales,
            month_income=period_income,
            no_available_days=not_available,
            saleRate=metrics.get("saleRate", {}).get("days", 0),
            availability=metrics.get("availability", "")
        )
    db.save_daily_stocks(today_stocks, datetime.now().date())

    date_range = [(start_date + timedelta(days=d))
                  for d in range(config.DIFF_DAYS_COUNT)]
    article_daily_data = {a: {} for a in articles}

    for day in date_range:
        day_stats = get_period_stats(token, articles, day, day)
        if not day_stats:
            continue

        for item in day_stats:
            article = item["nmID"]
            metrics = item.get("metrics", {})
            if not metrics:
                continue
            orders = metrics.get("ordersCount", 0)
            stocks = db.get_article_day_stocks(article, day.date()) or 0
            if article in article_daily_data:
                article_daily_data[article][day.date()] = (orders, stocks)

    sales_stats = []
    for art_data in articles_data:
        article = art_data.article
        mdata = month_data.get(article, {})

        days_stats = []
        for day in date_range:
            sales_count, stocks_count = article_daily_data.get(
                article, {}).get(day.date(), (0, 0))
            days_stats.append(
                DayStats(sales_count=sales_count, stocks_count=stocks_count))

        sales_stats.append(SalesStat(
            article=article,
            seller_article=art_data.seller_article,
            brand=art_data.brand,
            category=art_data.category,
            month_sales=mdata.get("month_sales", 0),
            cur_stocks=today_stocks.get(article, 0),
            middle_in_day_sales=mdata.get("middle_in_day_sales", 0.0),
            month_income=mdata.get("month_income", 0),
            no_available_days=mdata.get("no_available_days", 0),
            days_stats=days_stats,
            saleRate=mdata.get("saleRate", 0),
            availability=mdata.get("availability", "")
        ))

    return sales_stats


def convert_sales_stats_to_table(rconfig: _RunConfig,
                                 articles_data: list[utils.ArticleData],
                                 stats: list[SalesStat]) -> list[list]:
    base_columns = ["Артикул WB", "Артикул поставщика", "Бренд", "Категория"
                    "Всего продаж за месяц", "Остаток", "Среднее количество заказов в день",
                    "Выручка за 30 дней (руб)", "Товара нет в наличии (дней)"]
    last_columns = ["Оборачиваемость", "Доступность"]

    data = []
    data.append(["", "Дата обновления:",
                datetime.now().strftime(r"%Y-%m-%d %H:%M")])
    header_up = [""] * len(base_columns)
    for i in range(rconfig.DIFF_DAYS_COUNT, 0, -1):
        header_up += [f"{i} д. назад"] * 2
    header_up += [""] * len(last_columns)
    data.append(header_up)

    header_down = []
    header_down += base_columns
    for i in range(rconfig.DIFF_DAYS_COUNT):
        header_down += ["Заказы", "Остатки"]
    header_down += last_columns
    data.append(header_down)

    article_res = {}
    for i in stats:
        article_res[i.article] = i

    for i in articles_data:
        article = i.article
        if article not in article_res:
            data.append([])
        else:
            row = []
            stat: SalesStat = article_res[article]

            row.append(stat.article)
            row.append(stat.seller_article)
            row.append(stat.brand)
            row.append(stat.category)
            row.append(stat.month_sales)
            row.append(stat.cur_stocks)
            row.append(stat.middle_in_day_sales)
            row.append(stat.month_income)
            row.append(stat.no_available_days)

            for day_stat in stat.days_stats:
                row.append(day_stat.sales_count)
                row.append(day_stat.stocks_count)
            row.append(stat.saleRate)
            row.append(stat.availability)

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
    is_valid = False
    for _ in range(tryings):
        try:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body
            ).execute()
            is_valid = True
            break
        except:
            pass
    if not is_valid:
        logging.error("Google sheets access error")


def _period_sales_task_internal(rconfig: _RunConfig):
    articles_data = utils.get_article_data()
    if not articles_data:
        logging.error("No profitability articles")
        return
    token = utils.get_wb_token()
    if not token:
        logging.error("No wb token")
        return

    stats = read_sales_stats(token, rconfig, articles_data)
    if not stats:
        logging.error("Can't get stats")
        return
    google_data = convert_sales_stats_to_table(rconfig, articles_data, stats)
    save_sales_stats_to_sheet(google_data)


def period_sales_task():
    rconfig = _RunConfig(pconfig.DIFF_DAYS_COUNT, False)
    _period_sales_task_internal(rconfig)
