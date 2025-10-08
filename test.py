from parser import period_sales
from parser import utils
import config


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


def run_tests():
    tests = [token_read_test,
             articles_data_test,
             sales_stats_test,]
    results = []
    for test in tests:
        r = test()
        results.append(r)
    if all(results):
        print("ALL TESTS PASSED")


def main():
    run_tests()
    # period_sales.period_sales_task()


if __name__ == "__main__":
    main()
    # articles_data_test()
    # main()
    # period_sales.period_sales_task()
