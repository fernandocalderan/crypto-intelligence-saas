export type Asset = {
  symbol: string;
  name: string;
  category: string;
  price_usd: number;
  change_24h: number;
  volume_24h: number;
  momentum_score: number;
};

export type Signal = {
  id: string;
  signal_key: string;
  asset_symbol: string;
  signal_type: string;
  timeframe: string;
  direction: "bullish" | "bearish" | "neutral";
  confidence: number;
  score: number;
  thesis: string;
  evidence: string[];
  source: string;
  generated_at: string;
};

const apiUrl =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

const fallbackAssets: Asset[] = [
  {
    symbol: "BTC",
    name: "Bitcoin",
    category: "Layer 1",
    price_usd: 68420.45,
    change_24h: 3.4,
    volume_24h: 31200000000,
    momentum_score: 84.2
  },
  {
    symbol: "ETH",
    name: "Ethereum",
    category: "Layer 1",
    price_usd: 3628.18,
    change_24h: 2.1,
    volume_24h: 18600000000,
    momentum_score: 79.4
  },
  {
    symbol: "SOL",
    name: "Solana",
    category: "Layer 1",
    price_usd: 171.89,
    change_24h: 4.5,
    volume_24h: 6200000000,
    momentum_score: 88.6
  },
  {
    symbol: "DOGE",
    name: "Dogecoin",
    category: "Meme",
    price_usd: 0.194,
    change_24h: -2.6,
    volume_24h: 2100000000,
    momentum_score: 61
  },
  {
    symbol: "XRP",
    name: "XRP",
    category: "Payments",
    price_usd: 0.724,
    change_24h: -0.8,
    volume_24h: 1400000000,
    momentum_score: 58.4
  }
];

const fallbackSignals: Signal[] = [
  {
    id: "sig-btc-volume_spike",
    signal_key: "volume_spike",
    asset_symbol: "BTC",
    signal_type: "Volume Spike",
    timeframe: "4H",
    direction: "bullish",
    confidence: 78,
    score: 8.1,
    thesis: "BTC imprime un spike de volumen con expansión direccional y flujo nuevo.",
    evidence: ["volume ratio 1.86x over baseline", "24h price change +3.4%", "momentum score 84.2"],
    source: "mock",
    generated_at: new Date().toISOString()
  },
  {
    id: "sig-eth-range_breakout",
    signal_key: "range_breakout",
    asset_symbol: "ETH",
    signal_type: "Range Breakout",
    timeframe: "4H",
    direction: "bullish",
    confidence: 77,
    score: 7.9,
    thesis: "ETH sale de su rango de 20 días con confirmación de precio.",
    evidence: ["breakout margin 1.12% from 20d range", "range reference 3588.00", "volume ratio 1.45x"],
    source: "mock",
    generated_at: new Date().toISOString()
  },
  {
    id: "sig-sol-funding_extreme",
    signal_key: "funding_extreme",
    asset_symbol: "SOL",
    signal_type: "Funding Extreme",
    timeframe: "8H",
    direction: "bearish",
    confidence: 80,
    score: 8.4,
    thesis: "SOL muestra un extremo de funding con mercado demasiado cargado en longs.",
    evidence: ["funding rate +0.0310", "funding z-score 2.8", "OI change +11.4%"],
    source: "mock",
    generated_at: new Date().toISOString()
  },
  {
    id: "sig-doge-oi_divergence",
    signal_key: "oi_divergence",
    asset_symbol: "DOGE",
    signal_type: "OI Divergence",
    timeframe: "4H",
    direction: "bullish",
    confidence: 74,
    score: 7.6,
    thesis: "DOGE presenta divergencia entre precio y open interest con riesgo de squeeze.",
    evidence: ["price change -2.6%", "OI change +10.8%", "divergence spread 13.4 points"],
    source: "mock",
    generated_at: new Date().toISOString()
  },
  {
    id: "sig-xrp-liquidation_cluster",
    signal_key: "liquidation_cluster",
    asset_symbol: "XRP",
    signal_type: "Liquidation Cluster",
    timeframe: "1H",
    direction: "bullish",
    confidence: 79,
    score: 8.2,
    thesis: "XRP registra un cluster de liquidaciones de longs que limpia posicionamiento.",
    evidence: ["liquidation ratio 3.49x", "dominant side longs", "1h liquidations $22.0M"],
    source: "mock",
    generated_at: new Date().toISOString()
  }
];

async function fetchWithFallback<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${apiUrl}${path}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`Request failed for ${path}`);
    }

    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export function getAssets() {
  return fetchWithFallback<Asset[]>("/assets", fallbackAssets);
}

export function getSignals() {
  return fetchWithFallback<Signal[]>("/signals/live", fallbackSignals);
}
