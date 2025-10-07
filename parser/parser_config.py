import os
import googleapiclient.discovery
import httplib2
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2 import service_account

REQUEST_ATTEMPT_COUNT = 3
REQUEST_WAIT_SEC = 5

SALES_STATS_URL = "https://seller-analytics-api.wildberries.ru/api/v2/stocks-report/products/products"
SALES_URL = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
SALES_PERIOD_DAYS = 30
DIFF_DAYS_COUNT = 10
SALES_STATS_SHEET_NAME = "test"

PROFITABILITY_ARTICLES_RANGE = "A12:C"
PROFITABILITY_SHEET_NAME = "Рентабельность"

TOKEN_SHEET_NAME = "Токен"
TOKEN_RANGE = "A1:A1"

this_dir = os.path.dirname(os.path.realpath(__file__))
security_folder = os.path.join(this_dir, "security_settings")
creds_path = os.path.join(security_folder, "credentials.json")

token_path =  os.path.join(security_folder, "table_id.txt")
table_id = ""
with open(token_path, "r") as file:
    table_id = file.read().strip("\n, ")

scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_file(creds_path, scopes=scope)
service = build('sheets', 'v4', credentials=credentials)
