from fastapi import FastAPI
from contextlib import asynccontextmanager

from config import app
from parser.data import models
from tasks import register_tasks

@asynccontextmanager
async def lifespan(app: FastAPI):
    register_tasks()
    yield
    
app = FastAPI(lifespan=lifespan)



    