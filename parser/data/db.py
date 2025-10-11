import os
from datetime import date
from typing import Dict, Optional
from sqlalchemy import create_engine, Integer, Date, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_NAME = "table.db"

_sessionMaker = None


class Base(DeclarativeBase):
    pass


class DailyStock(Base):
    __tablename__ = "daily_stocks"
    article: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    stock_count: Mapped[int] = mapped_column(Integer, nullable=False)


def init_db(file_name: str = BASE_NAME):
    global _sessionMaker
    if _sessionMaker:
        return

    db_raw_path = os.path.join(THIS_DIR, file_name)
    db_path = f"sqlite:///{db_raw_path}"

    engine = create_engine(db_path, echo=False)
    _sessionMaker = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)


def get_session():
    if not _sessionMaker:
        init_db()
    return _sessionMaker()


def save_daily_stocks(stock_data: Dict[int, int], target_day: date):
    with get_session() as session:
        for article, count in stock_data.items():
            existing = session.get(DailyStock, (article, target_day))
            if existing:
                existing.stock_count = count
            else:
                session.add(DailyStock(article=article,
                            stock_count=count, day=target_day))
        session.commit()


def get_article_day_stocks(article: int, target_day: date) -> Optional[int]:
    with get_session() as session:
        stock = session.get(DailyStock, (article, target_day))
        return stock.stock_count if stock else None


def get_day_stocks(target_day: date) -> Dict[int, int]:
    with get_session() as session:
        stmt = select(DailyStock).where(DailyStock.day == target_day)
        rows = session.scalars(stmt).all()
        return {r.article: r.stock_count for r in rows}
