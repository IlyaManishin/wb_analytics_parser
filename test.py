from datetime import date, datetime, timedelta

from parser import period_sales, region_sales, voronka_stats
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


def period_sales_test() -> bool:
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

def region_sales_test() -> bool:
    token = utils.get_wb_token()
    if not token:
        print("Region sales test failed: can't read token")
        return False

    articles_data = utils.get_article_data()
    if not articles_data:
        print("Region sales test failed: no article data")
        return False

    end_date = datetime.today()
    start_date = end_date - timedelta(days=7)

    stats = region_sales.get_region_sales(start_date, end_date)
    if not stats:
        print("Region sales test failed: no stats returned")
        return False

    sample = stats[0]
    if not isinstance(sample.article, int) or not sample.city_name:
        print("Region sales test failed: invalid data structure")
        return False
    return True

def voronka_stats_test() -> bool:
    token = utils.get_wb_token()
    if not token:
        print("Voronka stats test failed: can't read token")
        return False

    articles_data = utils.get_article_data()
    if not articles_data:
        print("Voronka stats test failed: no article data")
        return False

    end_date = datetime.today()
    start_date = end_date - timedelta(days=7)

    stats = voronka_stats.get_voronka_stats(start_date, end_date)
    if not stats:
        print("Voronka stats test failed: no stats returned")
        return False

    sample = stats[0]
    if not isinstance(sample.article, int) or not sample.brand or not isinstance(sample.buyout_sum, float):
        print("Voronka stats test failed: invalid data structure")
        return False

    print("Voronka stats test passed")
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
        # token_read_test,
        # articles_data_test,
        period_sales_test,
        # # db_tests,
        # voronka_stats_test,
        # region_sales_test
    ]
    results = [test() for test in tests]
    if all(results):
        print("ALL TESTS PASSED")


def main():
    run_tests()


if __name__ == "__main__":
    main()
