from pydantic import BaseModel

class DayStats(BaseModel):
    sales_count: int
    difference: int

class SalesEntry(BaseModel):
    article: str
    brand: str
    month_sales: int
    middle_in_day_sales: int
    week_income: int
    no_available_days: int
    
    days_stats: list[DayStats]
    