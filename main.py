# ============================================================
# 📊 Krypto Backend – Institutionelle Datenanalyse API
# ============================================================

from fastapi import FastAPI
import requests, os
from dotenv import load_dotenv

# 🔐 Environment laden (.env oder Render Environment Variables)
load_dotenv()

app = FastAPI()
CMC_KEY = os.getenv("CMC_KEY")

# ============================================================
# 🪙 1️⃣ Einzelner Coin – Preis, Volumen, %Change
# ============================================================

@app.get("/api/price/{symbol}")
def get_price(symbol: str):
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
        params = {"symbol": symbol.upper()}

        r = requests.get(url, headers=headers, params=params)
        data = r.json()

        coin = data["data"][symbol.upper()]["quote"]["USD"]

        return {
            "status": "ok",
            "data": {
                "symbol": symbol.upper(),
                "price_usd": coin.get("price"),
                "volume_24h_usd": coin.get("volume_24h"),
                "change_24h_percent": coin.get("percent_change_24h")
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================================
# 🌍 2️⃣ Globaler Markt – Dominanz, MarketCap, Volumen
# ============================================================

@app.get("/api/global")
def get_global():
    try:
        url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
        r = requests.get(url, headers=headers)
        data = r.json()["data"]["quote"]["USD"]

        return {
            "status": "ok",
            "data": {
                "total_market_cap_usd": round(data.get("total_market_cap", 0), 2),
                "total_volume_24h_usd": round(data.get("total_volume_24h", 0), 2),
                "btc_dominance_percent": round(data.get("btc_dominance", 0), 2),
                "eth_dominance_percent": round(data.get("eth_dominance", 0), 2)
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================================
# 🧱 3️⃣ On-Chain & Market Data (CoinStats)
# ============================================================

@app.get("/api/onchain/{symbol}")
def get_onchain(symbol: str):
    try:
        symbol = symbol.upper()

        # Mapping Symbol → Coin-ID laut CoinStats
        id_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "BNB": "binance-coin",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "DOT": "polkadot",
            "MATIC": "matic-network"
        }

        coin_id = id_map.get(symbol, symbol.lower())
        url = f"https://api.coinstats.app/public/v1/coins/{coin_id}"

        r = requests.get(url)
        data = r.json()

        if "coin" not in data:
            return {"status": "error", "message": "Coin not found or invalid symbol"}

        coin = data["coin"]

        return {
            "status": "ok",
            "data": {
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "price_usd": coin.get("price"),
                "market_cap_usd": coin.get("marketCap"),
                "volume_24h_usd": coin.get("volume"),
                "available_supply": coin.get("availableSupply"),
                "total_supply": coin.get("totalSupply"),
                "price_change_1d": coin.get("priceChange1d"),
                "price_change_1w": coin.get("priceChange1w")
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================================
# 🧩 4️⃣ Kombinierter Dashboard Endpoint
# ============================================================

@app.get("/api/dashboard/{symbol}")
def get_dashboard(symbol: str):
    try:
        symbol = symbol.upper()
        CMC_KEY = os.getenv("CMC_KEY")

        # --- CoinMarketCap Daten
        cmc_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
        params = {"symbol": symbol}
        cmc_data = requests._
