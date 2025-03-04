import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from datetime import datetime
import json
import main

client = TestClient(app)  # FastAPI test client

class TestStockDataAPI(unittest.TestCase):

    def setUp(self):
        """Setup mock data before each test"""
        self.valid_stock_data = {
            "datetime": datetime.utcnow().isoformat(),
            "open": "100.5",
            "high": "105.2",
            "low": "99.3",
            "close": "102.7",
            "volume": 1500,
            "instrument": "AAPL"
        }

        self.invalid_stock_data = {
            "datetime": "invalid-date",  # Invalid datetime
            "open": "one hundred",  # Invalid decimal
            "high": 105.2,
            "low": 99.3,
            "close": 102.7,
            "volume": "thousand",  # Invalid int
            "instrument": "AAPL"
        }

@patch.object(main.db.stockdata, "find_many", new_callable=AsyncMock)
def test_get_data(self, mock_find_many):
    """Test fetching stock data"""
    mock_find_many.return_value = [self.valid_stock_data]  # Mock DB response

    response = client.get("/data")
    self.assertEqual(response.status_code, 200)
    self.assertIsInstance(response.json(), list)
    self.assertEqual(response.json()[0]["instrument"], "AAPL")

@patch.object(main.db.stockdata, "create", new_callable=AsyncMock)
def test_create_valid_stock(self, mock_create):
    """Test successful stock data creation"""
    mock_create.return_value = self.valid_stock_data  # Mock DB create response

    response = client.post("/data", json=self.valid_stock_data)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()["instrument"], self.valid_stock_data["instrument"])

@patch.object(main.db.stockdata, "find_many", new_callable=AsyncMock)
def test_strategy_performance(self, mock_find_many):
    """Test moving average strategy performance endpoint"""
    mock_find_many.return_value = [
        {
            "datetime": datetime.utcnow().isoformat(),
            "open": "100.0",
            "high": "110.0",
            "low": "95.0",
            "close": "105.0",
            "volume": 1500,
            "instrument": "AAPL"
        }
    ]  # Mock database response

    params = {"instrument": "AAPL", "short_window": 10, "long_window": 50}
    response = client.get("/strategy/performance", params=params)
    self.assertEqual(response.status_code, 200)
    self.assertIn("strategy", response.json())  # Ensure strategy key exists

if __name__ == "__main__":
    unittest.main()
