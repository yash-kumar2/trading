import pandas as pd
from prisma import Prisma
from datetime import datetime
from decimal import Decimal


db = Prisma()

async def insert_data():
    await db.connect()
 
    df = pd.read_excel("HINDALCO_1D.xlsx")
 
    df.columns = ["datetime", "open", "high", "low", "close", "volume", "instrument"]
    
    df["datetime"] = pd.to_datetime(df["datetime"])
  
    stock_data_list = df.to_dict(orient="records")
    
    for stock in stock_data_list:
        await db.stockdata.create(
            data={
                "datetime": stock["datetime"],
                "open": Decimal(stock["open"]),
                "high": Decimal(stock["high"]),
                "low": Decimal(stock["low"]),
                "close": Decimal(stock["close"]),
                "volume": int(stock["volume"]),
                "instrument": stock["instrument"],
            }
        )

    print("✅ Data inserted successfully into PostgreSQL!")
    await db.disconnect()


import asyncio
asyncio.run(insert_data())