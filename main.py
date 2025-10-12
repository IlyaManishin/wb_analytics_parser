from fastapi import FastAPI, Query
from contextlib import asynccontextmanager
from datetime import datetime

from tasks import register_tasks
from parser import voronka_stats
import logging


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("logger.log"),
    ]
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    register_tasks()
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/voronka-stats", response_model=list[voronka_stats.VoronkaStat])
def funnel_stats_handler(
    start_date: datetime = Query(..., description="Начало периода"),
    end_date: datetime = Query(..., description="Конец периода"),
):
    stats = voronka_stats.get_voronka_stats(start_date, end_date)
    return stats
