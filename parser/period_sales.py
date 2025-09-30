import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from pydantic import BaseModel

from . import parser_config as config
from . import utils
from . import parser_exceptions as exc


class DayStats(BaseModel):
    sales_count: int
    difference: int


class SalesStat(BaseModel):
    article: str
    brand: str
    month_sales: int
    middle_in_day_sales: int
    period_income: int
    no_available_days: int

    days_stats: list[DayStats]


class Sale(BaseModel):
    article: int
    date: datetime


def init_sales_entry(article: int, warehouseName: str, supplierArticle: str, subject: str, brand: str) -> SalesStat:
    entry = SalesStat(article=article,
                      brand=brand,
                      middle_in_day_sales=0, period_income=0, no_available_days=0,
                      days_stats=[])
    for i in range(config.SALES_PERIOD_DAYS + 1):
        entry.days_stats.append(DayStats(sales_count=0, difference=0))
    return entry


def init_empty_sales_entry(article: int):
    return init_sales_entry(article, "", "", "", "")


def get_period_stats(token: str, articles: list[int], start: datetime, end: datetime) -> list[dict]:
    all_items = []
    limit_size = 1000

    for i in range(0, len(articles), limit_size):
        batch = articles[i:i + limit_size]

        body = {
            "nmIDs": batch,
            "subjectID": 123456,
            "brandName": "Спортик",
            "tagID": 25345,
            "currentPeriod": {
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d")
            },
            "stockType": "mp",
            "skipDeletedNm": True,
            "orderBy": {
                "field": "avgOrders",
                "mode": "asc"
            },
            "availabilityFilters": [
                "deficient",
                "balanced"
            ],
            "limit": limit_size,
            "offset": 0
        }

        headers = utils.get_auth_header(token)
        result = utils.api_post(config.SALES_STATS_URL, headers, body)

        items = result.get("data", {}).get("items", [])
        if not items:
            break

        all_items += items

    return all_items


def get_month_sales(token: str) -> list[Sale]:
    now = datetime.now()
    header = utils.get_auth_header(token)
    url_time = (now - timedelta(days=30)
                ).strftime(r"%Y-%m-%d")
    url = f"{config.SALES_URL}?dateFrom={url_time}"

    resp = utils.api_get(url, header, config.REQUEST_ATTEMPT_COUNT)
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


def get_api_sales_data():
    pass


def get_sales_stats(token, articles: int) -> list[SalesStat]:
    now = datetime.now()

    end_date = now - timedelta(days=1)
    start_date = end_date - timedelta(days=config.SALES_PERIOD_DAYS + 1)

    month_stats = get_period_stats(token, articles, end_date - timedelta(days=30), end_date)
    month_sales = get_month_sales(token)

    date_range = [(start_date + timedelta(days=d)).date()
                for d in range(config.SALES_PERIOD_DAYS + 1)]  

    sales_by_article_date = {}
    for article in articles:
        sales_by_article_date[article] = {date: 0 for date in date_range}

    month_sales_by_article = {}
    for sale in month_sales:
        if sale.article in sales_by_article_date and sale.date in sales_by_article_date[sale.article]:
            sales_by_article_date[sale.article][sale.date] += 1

        if sale.article not in month_sales_by_article:
            month_sales_by_article[sale.article] = 0
        month_sales_by_article[sale.article] += 1

    sales_stats = []

    month_stats_dict = {item.get("nmID"): item for item in month_stats}

    for article_id in articles:
        item = month_stats_dict.get(article_id, {})
        brand = item.get("brandName", "")
        metrics = item.get("metrics", {})

        days_stats = []
        total_sales = 0

        article_sales = sales_by_article_date.get(article_id, {})

        sorted_dates = sorted(article_sales.keys())
        for i in range(1, len(sorted_dates)):  
            day_date = sorted_dates[i]
            prev_date = sorted_dates[i - 1]

            sales_count = article_sales[day_date]
            prev_sales_count = article_sales[prev_date]
            difference = sales_count - prev_sales_count

            total_sales += sales_count
            days_stats.append(DayStats(sales_count=sales_count, difference=difference))

        days_stats = days_stats[1:]

        sales_stat = SalesStat(
            article=str(article_id),
            brand=brand,
            month_sales=month_sales_by_article.get(article_id, 0),
            middle_in_day_sales=int(total_sales / max(len(days_stats), 1)),
            period_income=metrics.get("ordersSum", 0),
            no_available_days=sum(1 for ds in days_stats if ds.sales_count == 0),
            days_stats=days_stats
        )

        sales_stats.append(sales_stat)

    return sales_stats


def period_sales_task():
    articles = utils.get_profitability_articles()
    if not articles:
        logging.error("No profitability articles")
    token = utils.get_wb_token()
    if not token:
        logging.error("No wb token")

    res = get_sales_stats(token, articles)
    return res