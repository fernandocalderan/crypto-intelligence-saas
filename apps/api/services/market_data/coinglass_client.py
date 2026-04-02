from typing import Any


class CoinglassClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def fetch_liquidations(self, symbol: str) -> dict[str, Any] | None:
        if not self.api_key or self.api_key == "your-coinglass-api-key":
            return None

        # Optional integration point. If a real Coinglass key is configured later,
        # this client can be extended without changing the normalizer contract.
        return None
