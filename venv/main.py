from fastapi import FastAPI, HTTPException
from prisma import Prisma
from pydantic import BaseModel
from decimal import Decimal
from typing import List
from datetime import datetime

app = FastAPI()
db = Prisma()

class StockDataSchema(BaseModel):
    datetime: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    instrument: str

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


@app.get("/data", response_model=List[StockDataSchema])
async def get_data():
    records = await db.stockdata.find_many()
    return records


@app.post("/data", response_model=StockDataSchema)
async def create_data(stock: StockDataSchema):
    new_stock = await db.stockdata.create(
        data=stock.dict()
    )
    return new_stock
