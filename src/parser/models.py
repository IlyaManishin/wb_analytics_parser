from datetime import datetime
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

