from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from parser import period_sales


def add_task_at(scheduler: BackgroundScheduler, task, hour, minute):
    trigger = CronTrigger(hour=hour, minute=minute)
    scheduler.add_job(task, trigger)


def register_tasks():
    logging.info("Run regular tasks")

    scheduler = BackgroundScheduler()
    add_task_at(scheduler, period_sales.period_sales_task, 6, 0)

    scheduler.start()
