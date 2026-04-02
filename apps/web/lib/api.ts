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
  asset_symbol: string;
  signal_type: string;
  timeframe: string;
  confidence: number;
  score: number;
  thesis: string;
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
    change_24h: 2.8,
    volume_24h: 29850000000,
    momentum_score: 84.2
  },
  {
    symbol: "ETH",
    name: "Ethereum",
    category: "Layer 1",
    price_usd: 3520.18,
    change_24h: 1.6,
    volume_24h: 15400000000,
    momentum_score: 78.4
  },
  {
    symbol: "SOL",
    name: "Solana",
    category: "Layer 1",
    price_usd: 171.89,
    change_24h: 4.2,
    volume_24h: 6200000000,
    momentum_score: 88.6
  }
];

const fallbackSignals: Signal[] = [
  {
    id: "sig-btc-breakout",
    asset_symbol: "BTC",
    signal_type: "Momentum Breakout",
    timeframe: "4H",
    confidence: 89,
    score: 92,
    thesis: "Expansión de volumen y ruptura de rango con funding todavía controlado.",
    generated_at: new Date().toISOString()
  },
  {
    id: "sig-sol-relative-strength",
    asset_symbol: "SOL",
    signal_type: "Relative Strength",
    timeframe: "1D",
    confidence: 82,
    score: 86,
    thesis: "Mejor comportamiento relativo frente a majors con continuidad de tendencia.",
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
  return fetchWithFallback<Signal[]>("/signals", fallbackSignals);
}
