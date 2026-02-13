from datetime import date
from typing import Optional
from pydantic import BaseModel

class WbPeriod(BaseModel):
    start: date
    end: date

    def to_dict(self):
        res = {
            "start": self.start.strftime(r"%Y-%m-%d"),
            "end": self.end.strftime(r"%Y-%m-%d"),
        }
        return res

class AdvancedPeriodBody(BaseModel):
    selected: WbPeriod
    past: Optional[WbPeriod] = None

class FinanceReportRequest(BaseModel):
    spreadsheets_id: str
    token: str
    sheet_name: str
    start_date: date
    end_date: date
