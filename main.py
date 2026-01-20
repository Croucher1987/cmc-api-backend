# ============================================================
# 📊 Krypto Backend – Institutionelle Datenanalyse API
# ============================================================

from fastapi import FastAPI
import requests, os, time, logging
from functools import lru_cache
from dotenv import load_dotenv

# 🔐 Environment laden (.env oder Render Environment Variables)
load_dotenv()
app = FastAPI()

CMC_KEY = os.getenv("CMC_KEY")
COINGLASS_KEY = os.getenv("COINGLASS_API_KEY")

# ============================================================
# 🧠 Logging – zeigt jede Anfrage im Render-Log
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@app.middleware("http")
async def log_requests(request, call_next):
    logging.info(f"📩 Request: {request.method} {request.url}")
    start_time = time.time()
    response = await call_next(request)
    duration = round(time.time() - start_time, 2)
    logging.info(f"📤 Response: {response.status_code} in {duration}s")
    return response


# ============================================================
# ⚡ Cache – vermeidet wiederholte API-Abfragen (1 Minütig)
# ============================================================
CACHE_TTL = 60  # Sekunden
_cache_store = {}

def cache_get(key):
    entry = _cache_store.get(key)
    if entry and (time.time() - entry["time"]) < CACHE_TTL:
        return entry["data"]
    return None

def cache_set(key, data):
    _cache_store[key] = {"data": data, "time": time.time()}


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
        id_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "BNB": "binance-coin", "XRP": "ripple", "ADA": "cardano",
            "DOGE": "dogecoin", "AVAX": "avalanche-2", "DOT": "polkadot", "MATIC": "matic-network"
        }
        coin_id = id_map.get(symbol.upper(), symbol.lower())
        url = f"https://api.coinstats.app/public/v1/coins/{coin_id}"

        r = requests.get(url)
        data = r.json()
        coin = data.get("coin", {})

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
# 🧱 Derivate – Coinglass (Funding, OI, Liquidations)
# ============================================================
@app.get("/api/derivatives/{symbol}")
def get_derivatives(symbol: str):
    try:
        base_url = "https://open-api.coinglass.com/api/pro/v1"
        headers = {"coinglassSecret": COINGLASS_KEY}
        symbol = symbol.upper()

        funding_url = f"{base_url}/futures/funding_rates?symbol={symbol}"
        oi_url = f"{base_url}/futures/openInterest?symbol={symbol}"
        liq_url = f"{base_url}/futures/liquidation_chart?symbol={symbol}"

        funding_data = requests.get(funding_url, headers=headers).json()
        oi_data = requests.get(oi_url, headers=headers).json()
        liq_data = requests.get(liq_url, headers=headers).json()

        result = {
            "symbol": symbol,
            "funding_rate": funding_data.get("data", [{}])[0].get("fundingRate"),
            "open_interest_change_24h": oi_data.get("data", {}).get("openInterestChange24h"),
            "liquidations_total_usd": liq_data.get("data", {}).get("totalVolUsd")
        }
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# 💬 Sentiment – Fear & Greed Index
# ============================================================
@app.get("/api/sentiment")
def get_sentiment():
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        data = requests.get(url).json()["data"][0]
        return {
            "status": "ok",
            "data": {
                "value": int(data["value"]),
                "classification": data["value_classification"],
                "timestamp": data["timestamp"]
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# 💵 Makro – DXY, Nasdaq, Gold, VIX
# ============================================================
@app.get("/api/macro")
def get_macro():
    try:
        assets = {"DXY": "DX-Y.NYB", "NASDAQ": "^NDX", "GOLD": "GC=F", "VIX": "^VIX"}
        results = {}
        for key, ticker in assets.items():
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            r = requests.get(url).json()
            meta = r.get("chart", {}).get("result", [{}])[0].get("meta", {})
            results[key] = {
                "symbol": ticker,
                "price": meta.get("regularMarketPrice"),
                "currency": meta.get("currency"),
                "exchange": meta.get("exchangeName")
            }
        return {"status": "ok", "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# 📊 Extended Dashboard Endpoint (kombiniert alles)
# ============================================================
@app.get("/api/dashboard/extended/{symbol}")
def get_extended_dashboard(symbol: str):
    try:
        symbol = symbol.upper()
        cache_key = f"extended_{symbol}"
        cached = cache_get(cache_key)
        if cached:
            return {"status": "ok", "cached": True, "data": cached}

        data = {
            "symbol": symbol,
            "timestamp": int(time.time()),
            "price": get_price(symbol).get("data", {}),
            "global": get_global().get("data", {}),
            "onchain": get_onchain(symbol).get("data", {}),
            "derivatives": get_derivatives(symbol).get("data", {}),
            "sentiment": get_sentiment().get("data", {}),
            "macro": get_macro().get("data", {})
        }
        cache_set(cache_key, data)
        return {"status": "ok", "cached": False, "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# 🧮 Bias Score Endpoint – Marktstimmung (-5 bis +5)
# ============================================================
@app.get("/api/bias/{symbol}")
def get_bias(symbol: str):
    try:
        symbol = symbol.upper()
        d = get_derivatives(symbol)
        s = get_sentiment()
        m = get_macro()
        p = get_price(symbol)

        funding = d.get("data", {}).get("funding_rate") or 0
        oi = d.get("data", {}).get("open_interest_change_24h") or 0
        fear = s.get("data", {}).get("value") or 50
        dxy = m.get("data", {}).get("DXY", {}).get("price") or 100
        vix = m.get("data", {}).get("VIX", {}).get("price") or 15
        pc = p.get("data", {}).get("change_24h_percent") or 0

        score = 0
        if funding > 0: score += 1
        elif funding < 0: score -= 1
        if oi > 1: score += 0.5
        elif oi < -1: score -= 0.5
        if fear >= 60: score += 1
        elif fear <= 40: score -= 1
        if dxy > 105: score -= 1
        elif dxy < 100: score += 1
        if vix > 18: score -= 0.5
        elif vix < 13: score += 0.5
        if pc > 0: score += 1
        elif pc < 0: score -= 1
        score = max(min(score, 5), -5)

        label = "Neutral"
        if score >= 3: label = "Bullish"
        elif score <= -3: label = "Bearish"

        return {"status": "ok", "data": {
            "symbol": symbol,
            "bias_score": round(score, 2),
            "classification": label,
            "inputs": {"funding_rate": funding, "oi_change_24h": oi, "fear": fear, "dxy": dxy, "vix": vix, "price_change_24h": pc}
        }}
    except Exception as e:
        return {"status": "error", "message": str(e)}
