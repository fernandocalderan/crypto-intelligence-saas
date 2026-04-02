from datetime import datetime, timezone
from typing import Any

import httpx


class BinanceClient:
    def __init__(self, base_url: str = "https://fapi.binance.com") -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = 10.0

    def _request(self, path: str, params: dict[str, Any]) -> Any:
        response = httpx.get(
            f"{self.base_url}{path}",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def fetch_ohlcv(self, symbol: str, interval: str = "1d", limit: int = 20) -> list[dict[str, Any]]:
        payload = self._request(
            "/fapi/v1/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
        )
        return [
            {
                "open_time": datetime.fromtimestamp(item[0] / 1000, tz=timezone.utc),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
                "close_time": datetime.fromtimestamp(item[6] / 1000, tz=timezone.utc),
            }
            for item in payload
        ]

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        payload = self._request("/fapi/v1/ticker/24hr", {"symbol": symbol})
        return {
            "symbol": payload["symbol"],
            "last_price": float(payload["lastPrice"]),
            "price_change_percent": float(payload["priceChangePercent"]),
            "volume": float(payload["volume"]),
            "quote_volume": float(payload["quoteVolume"]),
            "close_time": datetime.fromtimestamp(payload["closeTime"] / 1000, tz=timezone.utc),
        }

    def fetch_funding(self, symbol: str) -> dict[str, Any]:
        payload = self._request("/fapi/v1/fundingRate", {"symbol": symbol, "limit": 1})
        latest = payload[0] if payload else {}
        if not latest:
            return {}
        return {
            "funding_rate": float(latest["fundingRate"]),
            "timestamp": datetime.fromtimestamp(latest["fundingTime"] / 1000, tz=timezone.utc),
        }

    def fetch_open_interest(self, symbol: str) -> dict[str, Any]:
        payload = self._request("/fapi/v1/openInterest", {"symbol": symbol})
        return {
            "open_interest": float(payload["openInterest"]),
            "symbol": payload["symbol"],
            "timestamp": datetime.now(timezone.utc),
        }
