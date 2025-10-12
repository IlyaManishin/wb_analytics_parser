import os
from datetime import date, datetime

from parser import period_sales
from parser import utils
from parser.data import db


def token_read_test() -> bool:
    token = utils.get_wb_token()
    if not token or len(token) < 10:
        print("Can't read token")
        return False
    return True


def articles_data_test() -> bool:
    data = utils.get_article_data()
    if len(data) == 0:
        print("Can't get article data in profitability")
        return False
    return True


def sales_stats_test() -> bool:
    articles_data = utils.get_article_data()
    token = utils.get_wb_token()
    if not articles_data or not token:
        return False

    config = period_sales._RunConfig(1, True)
    stats = period_sales.read_sales_stats(token, config, articles_data)
    if not stats:
        print("Sale stats error")
        return False
    return True


def db_tests() -> bool:
    db.init_test_db()
    today = date.today()

    db.save_daily_stocks({123: 10}, today)
    if db.get_article_day_stocks(123, today) != 10:
        print("DB test failed: save/get single")
        return False

    db.save_daily_stocks({123: 20}, today)
    if db.get_article_day_stocks(123, today) != 20:
        print("DB test failed: update existing")
        return False

    db.save_daily_stocks({1: 5, 2: 7, 3: 9}, today)
    all_stocks = db.get_day_stocks(today)
    expected = {1: 5, 2: 7, 3: 9}
    if not all(all_stocks.get(k) == v for k, v in expected.items()):
        print(f"DB test failed: multiple articles (got {all_stocks})")
        return False

    return True


def run_tests():
    tests = [
        token_read_test,
        articles_data_test,
        sales_stats_test,
        db_tests
    ]
    results = [test() for test in tests]
    if all(results):
        print("ALL TESTS PASSED")


def main():
    run_tests()
    # period_sales.period_sales_task()


if __name__ == "__main__":
    main()
