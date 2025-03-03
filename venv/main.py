from fastapi import FastAPI, HTTPException
from prisma import Prisma
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd

import json
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
@app.get("/strategy/performance")
async def get_strategy_performance(instrument: str = None, short_window: int = 20, long_window: int = 50):
   
    try:
        # Query data
        query = {}
        if instrument:
            query["instrument"] = instrument
            
        records = await db.stockdata.find_many(
            where=query,
            order=[
                {"instrument": "asc"},
                {"datetime": "asc"}
            ]
        )
        
        if not records:
            raise HTTPException(status_code=404, detail="No stock data found")
        
        # Convert to pandas DataFrame for easier manipulation
        data = []
        for record in records:
            data.append({
                "datetime": record.datetime,
                "open": float(record.open),
                "high": float(record.high),
                "low": float(record.low),
                "close": float(record.close),
                "volume": record.volume,
                "instrument": record.instrument
            })
        
        df = pd.DataFrame(data)
        
        # Group by instrument to handle multiple instruments
        grouped = df.groupby('instrument')
        
        results = []
        
        for instrument_name, group in grouped:
         
            group = group.sort_values('datetime')
            
          
            group['short_ma'] = group['close'].rolling(window=short_window).mean()
            group['long_ma'] = group['close'].rolling(window=long_window).mean()
            
          
            group['signal'] = 0.0
            group['signal'][short_window:] = (group['short_ma'][short_window:] > 
                                            group['long_ma'][short_window:]).astype(int)
            
           
            group['position'] = group['signal'].diff()
            
          
            group['returns'] = group['close'].pct_change()
            
         
            group['strategy_returns'] = group['returns'] * group['signal'].shift(1)
            
           
            signals = []
            buy_points = group[group['position'] == 1]
            sell_points = group[group['position'] == -1]
            
            for idx, row in buy_points.iterrows():
                signals.append({
                    "datetime": row['datetime'].isoformat(),
                    "price": row['close'],
                    "action": "BUY"
                })
                
            for idx, row in sell_points.iterrows():
                signals.append({
                    "datetime": row['datetime'].isoformat(),
                    "price": row['close'],
                    "action": "SELL"
                })
            
            # Sort signals by datetime
            signals = sorted(signals, key=lambda x: x['datetime'])
            
            # Calculate performance metrics
            total_trades = len(signals)
            winning_trades = len(group[group['strategy_returns'] > 0])
            losing_trades = len(group[group['strategy_returns'] < 0])
            
            # Calculate cumulative returns
            cumulative_returns = (1 + group['returns']).cumprod() - 1
            strategy_cumulative_returns = (1 + group['strategy_returns'].fillna(0)).cumprod() - 1
            
            # Calculate max drawdown
            peak = strategy_cumulative_returns.expanding(min_periods=1).max()
            drawdown = (strategy_cumulative_returns - peak) / (1 + peak)
            max_drawdown = drawdown.min()
            
            # Calculate Sharpe ratio (assuming 252 trading days in a year)
            sharpe_ratio = (group['strategy_returns'].mean() / group['strategy_returns'].std()) * (252 ** 0.5) if group['strategy_returns'].std() != 0 else 0
            
            # Prepare performance metrics
            performance = {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
                "final_return": float(strategy_cumulative_returns.iloc[-1]) if not strategy_cumulative_returns.empty else 0,
                "buy_hold_return": float(cumulative_returns.iloc[-1]) if not cumulative_returns.empty else 0,
                "max_drawdown": float(max_drawdown) if not pd.isna(max_drawdown) else 0,
                "sharpe_ratio": float(sharpe_ratio)
            }
            
            results.append({
                "instrument": instrument_name,
                "signals": signals,
                "performance": performance
            })
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating strategy performance: {str(e)}")
