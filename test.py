from parser import period_sales
from parser import utils
import config

def prof_articles_test():
    articles = utils.get_profitability_articles()
    if not articles or len(articles) == 0:
        print("prof_articles_test error: no articles")
    # print(articles[:100])


def token_read_test():
    token = utils.get_wb_token()
    if not token or len(token) < 10:
        print("Can't read token")


def run_tests():
    prof_articles_test()
    token_read_test()


def main():
    run_tests()
    # period_sales.period_sales_task()


if __name__ == "__main__":
    period_sales.period_sales_task()
