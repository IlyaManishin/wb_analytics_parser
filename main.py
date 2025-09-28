from fastapi import FastAPI

from parser import period_sales
from parser.data import models


app = FastAPI()

@app.post("period-sales")
def get_period_sales(token: str) -> list[models.SalesEntry]:
    return []