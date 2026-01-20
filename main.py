from fastapi import FastAPI
import requests, os
from dotenv import load_dotenv

# 🔐 .env-Datei laden
load_dotenv()

app = FastAPI()
CMC_KEY = os.getenv("CMC_KEY")

# ============================================================
# 🪙 EINZELNER COIN-ENDPOINT (z. B. /api/price/BTC)
# ============================================================

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

# ============================================================
# 🌍 GLOBALER MARKT-ENDPOINT (z. B. /api/global)
# ============================================================

@app.get("/api/global")
def get_global_data():
    try:
        url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
        response = requests.get(url, headers=headers)
        data = response.json()

        global_data = data["data"]
        usd_data = global_data["quote"]["USD"]

        result = {
            "total_market_cap_usd": round(usd_data["total_market_cap"], 2),
            "total_volume_24h_usd": round(usd_data["total_volume_24h"], 2),
            "btc_dominance_percent": round(global_data["btc_dominance"], 2),
            "eth_dominance_percent": round(global_data["eth_dominance"], 2),
            "active_cryptocurrencies": global_data["active_cryptocurrencies"],
            "last_updated": global_data["last_updated"]
        }

        return {"status": "ok", "data": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}
# ============================================================
# 🧱 On-Chain Data via CryptoQuant (BTC, ETH etc.)
# ============================================================

@app.get("/api/onchain/{symbol}")
def get_onchain_data(symbol: str):
    try:
        # CryptoQuant bietet öffentliche On-Chain-Daten an
        symbol = symbol.upper()

        # Beispielhafte Kernmetriken
        endpoints = {
            "realized_cap": f"https://api.cryptoquant.com/v1/{symbol.lower()}-market/realized-cap",
            "sopr": f"https://api.cryptoquant.com/v1/{symbol.lower()}-market/sopr",
            "nupl": f"https://api.cryptoquant.com/v1/{symbol.lower()}-market/nupl"
        }

        results = {}
        for key, url in endpoints.items():
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                # Nur letzte 10 Werte behalten, um Antwort kompakt zu halten
                results[key] = data[-10:] if isinstance(data, list) else data
            else:
                results[key] = {"error": f"Request failed: {r.status_code}"}

        return {"status": "ok", "symbol": symbol, "data": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}
