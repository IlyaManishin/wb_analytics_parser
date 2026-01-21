from typing import Optional
from fastapi import FastAPI, Query, Body
from contextlib import asynccontextmanager
from datetime import datetime

from tasks import register_tasks
from parser import voronka_stats, region_sales
from parser import models as p_models


class AdvancedPeriodBody(p_models.BaseModel):
    selected: p_models.WbPeriod
    past: Optional[p_models.WbPeriod] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_tasks()
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/voronka-stats", response_model=list[voronka_stats.VoronkaStat])
def voronka_stats_handler(
    spreadsheets_id: str = Query(..., description="Id таблицы"),
    start_date: datetime = Query(..., description="Начало периода"),
    end_date: datetime = Query(..., description="Конец периода"),
):
    period = p_models.WbPeriod(start=start_date, end=end_date)
    stats = voronka_stats.get_voronka_stats(spreadsheets_id, period)
    return stats

@app.post("/voronka-adv-stats", response_model=list[voronka_stats.VoronkaAdvancedStat])
def voronka_advanced_stats_handler(
    spreadsheets_id: str = Query(..., description="ID таблицы"),
    body: AdvancedPeriodBody = Body(..., description="Периоды: selected и past")
):
    stats = voronka_stats.get_advanced_voronka_stats(
        spreadsheets_id=spreadsheets_id,
        selected=body.selected,
        past=body.past
    )
    return stats


@app.get("/region-sales", response_model=list[region_sales.RegionSale])
def region_stats_handler(
    spreadsheets_id: str = Query(..., description="Id таблицы"),
    start_date: datetime = Query(..., description="Начало периода"),
    end_date: datetime = Query(..., description="Конец периода"),
):
    period = p_models.WbPeriod(start=start_date, end=end_date)
    stats = region_sales.get_region_sales(spreadsheets_id, period)
    return stats
