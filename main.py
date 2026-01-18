from fastapi import FastAPI
import requests, os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
CMC_KEY = os.getenv("CMC_KEY")

@app.get("/api/price/{symbol}")
def get_price(symbol: str):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
    params = {"symbol": symbol}
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    return {
        "symbol": symbol,
        "price": data["data"][symbol]["quote"]["USD"]["price"],
        "volume": data["data"][symbol]["quote"]["USD"]["volume_24h"],
        "change_24h": data["data"][symbol]["quote"]["USD"]["percent_change_24h"]
    }
