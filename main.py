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
        cmc_data = requests.get(cmc_url, headers=headers, params=params).json()
        coin = cmc_data["data"][symbol]["quote"]["USD"]

        # --- Global Metrics
        global_url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
        global_data = requests.get(global_url, headers=headers).json()["data"]["quote"]["USD"]

        # --- On-Chain via CoinStats
        id_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "BNB": "binance-coin", "XRP": "ripple", "ADA": "cardano",
            "DOGE": "dogecoin", "AVAX": "avalanche-2", "DOT": "polkadot"
        }
        coin_id = id_map.get(symbol, symbol.lower())
        cs_url = f"https://api.coinstats.app/public/v1/coins/{coin_id}"
        cs_data = requests.get(cs_url).json().get("coin", {})

        return {
            "status": "ok",
            "symbol": symbol,
            "data": {
                "price_usd": coin.get("price"),
                "change_24h_percent": coin.get("percent_change_24h"),
                "volume_24h_usd": coin.get("volume_24h"),
                "market_cap_usd": coin.get("market_cap"),
                "global": {
                    "total_market_cap_usd": global_data.get("total_market_cap"),
                    "btc_dominance_percent": global_data.get("btc_dominance"),
                    "eth_dominance_percent": global_data.get("eth_dominance")
                },
                "onchain": {
                    "available_supply": cs_data.get("availableSupply"),
                    "total_supply": cs_data.get("totalSupply"),
                    "price_change_1d": cs_data.get("priceChange1d"),
                    "price_change_1w": cs_data.get("priceChange1w")
                }
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
        
# ============================================================
# 💹 5️⃣ Multi-Coin Endpoint – Top 100 Coins (dynamisch)
# ============================================================

@app.get("/api/multi")
def get_multi(limit: int = 100):
    """
    Gibt Marktdaten für mehrere Coins gleichzeitig zurück.
    Optionaler Parameter ?limit=10 (Standard = 100)
    """
    try:
        CMC_KEY = os.getenv("CMC_KEY")
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
        params = {"start": 1, "limit": limit, "convert": "USD"}

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if "data" not in data:
            return {"status": "error", "message": "Invalid response from API"}

        result = []
        for coin in data["data"]:
            result.append({
                "rank": coin.get("cmc_rank"),
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "price_usd": round(coin["quote"]["USD"]["price"], 4),
                "volume_24h_usd": round(coin["quote"]["USD"]["volume_24h"], 2),
                "change_24h_percent": round(coin["quote"]["USD"]["percent_change_24h"], 2),
                "market_cap_usd": round(coin["quote"]["USD"]["market_cap"], 2)
            })

        return {"status": "ok", "total": len(result), "data": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================================
# 🧱 Derivate Endpoint – Coinglass (Funding, OI, Liquidations)
# ============================================================

@app.get("/api/derivatives/{symbol}")
def get_derivatives(symbol: str):
    """
    Liefert Funding Rate, Open Interest & Liquidations für das Symbol.
    Quelle: Coinglass API
    """
    try:
        COINGLASS_KEY = os.getenv("COINGLASS_API_KEY")
        base_url = "https://open-api.coinglass.com/api/pro/v1"
        headers = {"coinglassSecret": COINGLASS_KEY}
        symbol = symbol.upper()

        # Funding Rates
        funding_url = f"{base_url}/futures/funding_rates?symbol={symbol}"
        funding_data = requests.get(funding_url, headers=headers).json()

        # Open Interest
        oi_url = f"{base_url}/futures/openInterest?symbol={symbol}"
        oi_data = requests.get(oi_url, headers=headers).json()

        # Liquidations
        liq_url = f"{base_url}/futures/liquidation_chart?symbol={symbol}"
        liq_data = requests.get(liq_url, headers=headers).json()

        result = {
            "symbol": symbol,
            "funding_rate": funding_data.get("data", [{}])[0].get("fundingRate"),
            "funding_rate_avg_24h": funding_data.get("data", [{}])[0].get("fundingRate24hAvg"),
            "open_interest_usd": oi_data.get("data", {}).get("openInterest"),
            "open_interest_change_24h": oi_data.get("data", {}).get("openInterestChange24h"),
            "liquidations_long_usd": liq_data.get("data", {}).get("longVolUsd"),
            "liquidations_short_usd": liq_data.get("data", {}).get("shortVolUsd"),
            "liquidations_total_usd": liq_data.get("data", {}).get("totalVolUsd")
        }

        return {"status": "ok", "data": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# 💬 Sentiment Endpoint – Fear & Greed Index (Alternative.me)
# ============================================================

@app.get("/api/sentiment")
def get_sentiment():
    """
    Liefert den aktuellen Fear & Greed Index (0–100).
    Quelle: https://api.alternative.me/fng/
    """
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url).json()

        if "data" not in response:
            return {"status": "error", "message": "Invalid response from API"}

        data = response["data"][0]
        result = {
            "value": int(data["value"]),
            "classification": data["value_classification"],
            "timestamp": data["timestamp"]
        }

        return {"status": "ok", "data": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}
