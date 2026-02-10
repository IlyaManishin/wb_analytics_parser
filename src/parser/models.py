from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class WbPeriod(BaseModel):
    start: datetime
    end: datetime

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
    sheet_name: str
    start_date: datetime
    end_date: datetime
