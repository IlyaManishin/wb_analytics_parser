import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
import socket

# PORT = 8000

REQUEST_ATTEMPT_COUNT = 3
REQUEST_WAIT_SEC = 5

#____COMMON_DATA___
SOCKET_WAIT_SEC = 500
WB_CARDS_LIST_URL = "https://content-api.wildberries.ru/content/v2/get/cards/list"
CARDS_WAIT_TIME = 15

# ____SALES_STATS___
SALES_STATS_URL = "https://seller-analytics-api.wildberries.ru/api/v2/stocks-report/products/products"
SALES_URL = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
SALES_PERIOD_DAYS = 30
DIFF_DAYS_COUNT = 10
SALES_STATS_SHEET_NAME = "Продажи 10 дней"

# ____VORONKA_STATS____
VORONKA_URL = "https://seller-analytics-api.wildberries.ru/api/analytics/v3/sales-funnel/products"

# ____STOCKS_STATS____
OFFICES_URL = "https://marketplace-api.wildberries.ru/api/v3/offices"

WB_WAREHOUSE_REMAINS_URL = "https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains"
WB_WAREHOUSE_STATUS_URL = "https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains/tasks/{task_id}/status"
WB_WAREHOUSE_DOWNLOAD_URL = "https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains/tasks/{task_id}/download"
WB_STATUS_ATTEMPTS = 30

# ____REGION_STATS____
REGION_SALE_URL = "https://seller-analytics-api.wildberries.ru/api/v1/analytics/region-sale"

PROFITABILITY_ARTICLES_RANGE = "A12:D"
PROFITABILITY_SHEET_NAME = "Рентабельность"

TOKEN_SHEET_NAME = "Токен"
TOKEN_RANGE = "A1:A1"

# ____FINANCE_REPORT____
WB_REPORT_URL = "https://statistics-api.wildberries.ru/api/v5/supplier/reportDetailByPeriod"
FIN_REPORT_ATTEMPTS = 2
FIN_REPORT_WAIT_TIME = 30
FIN_REPORT_RANGE = "E:ZZ"


PARSER_DIR = os.path.dirname(os.path.realpath(__file__))
security_folder = os.path.join(PARSER_DIR, "security_settings")
creds_path = os.path.join(security_folder, "credentials.json")

token_path = os.path.join(security_folder, "table_id.txt")

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

socket.setdefaulttimeout(SOCKET_WAIT_SEC) 
credentials = service_account.Credentials.from_service_account_file(
    creds_path, scopes=scope)
service = build('sheets', 'v4', credentials=credentials)
