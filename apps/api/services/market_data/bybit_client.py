from datetime import datetime, timezone
from typing import Any

import httpx


class BybitClient:
    def __init__(self, base_url: str = "https://api.bybit.com") -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = 10.0

    def _request(self, path: str, params: dict[str, Any]) -> Any:
        response = httpx.get(
            f"{self.base_url}{path}",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("retCode") != 0:
            raise RuntimeError(payload.get("retMsg", "Unknown Bybit error"))
        return payload.get("result", {})

    def fetch_ohlcv(self, symbol: str, interval: str = "D", limit: int = 20) -> list[dict[str, Any]]:
        result = self._request(
            "/v5/market/kline",
            {"category": "linear", "symbol": symbol, "interval": interval, "limit": limit},
        )
        raw_rows = result.get("list", [])
        rows = sorted(raw_rows, key=lambda item: int(item[0]))
        return [
            {
                "open_time": datetime.fromtimestamp(int(item[0]) / 1000, tz=timezone.utc),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
            }
            for item in rows
        ]

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        result = self._request(
            "/v5/market/tickers",
            {"category": "linear", "symbol": symbol},
        )
        ticker = (result.get("list") or [{}])[0]
        return {
            "symbol": ticker.get("symbol", symbol),
            "last_price": float(ticker.get("lastPrice", 0.0)),
            "price_change_percent": float(ticker.get("price24hPcnt", 0.0)) * 100.0,
            "volume": float(ticker.get("volume24h", 0.0)),
            "quote_volume": float(ticker.get("turnover24h", 0.0)),
            "open_interest": float(ticker.get("openInterest", 0.0)),
            "funding_rate": float(ticker.get("fundingRate", 0.0)),
            "next_funding_time": ticker.get("nextFundingTime"),
        }

    def fetch_funding(self, symbol: str) -> dict[str, Any]:
        result = self._request(
            "/v5/market/funding/history",
            {"category": "linear", "symbol": symbol, "limit": 1},
        )
        latest = (result.get("list") or [{}])[0]
        if not latest:
            return {}
        return {
            "funding_rate": float(latest.get("fundingRate", 0.0)),
            "timestamp": datetime.fromtimestamp(
                int(latest["fundingRateTimestamp"]) / 1000,
                tz=timezone.utc,
            ),
        }

    def fetch_open_interest(self, symbol: str) -> dict[str, Any]:
        result = self._request(
            "/v5/market/open-interest",
            {
                "category": "linear",
                "symbol": symbol,
                "intervalTime": "5min",
                "limit": 2,
            },
        )
        rows = sorted(result.get("list", []), key=lambda item: int(item["timestamp"]), reverse=True)
        current = rows[0] if rows else {}
        previous = rows[1] if len(rows) > 1 else {}
        current_value = float(current.get("openInterest", 0.0))
        previous_value = float(previous.get("openInterest", 0.0))
        change_pct = 0.0
        if previous_value:
            change_pct = ((current_value - previous_value) / previous_value) * 100.0

        return {
            "open_interest": current_value,
            "previous_open_interest": previous_value,
            "open_interest_change_pct": change_pct,
            "timestamp": datetime.fromtimestamp(
                int(current.get("timestamp", int(datetime.now(timezone.utc).timestamp() * 1000))) / 1000,
                tz=timezone.utc,
            ),
        }
