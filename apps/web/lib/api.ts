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

export type SignalFeed = {
  access_plan: "free" | "pro" | "pro_plus";
  total_available: number;
  visible_count: number;
  has_locked_signals: boolean;
  signals: Signal[];
};

export type MarketSnapshot = {
  symbol: string;
  name: string;
  category: string;
  source: string;
  timeframe: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  price_usd: number;
  change_24h: number;
  volume_24h: number;
  avg_volume_24h: number;
  range_high_20d: number;
  range_low_20d: number;
  funding_rate: number;
  funding_zscore: number;
  open_interest: number;
  oi_change_24h: number;
  long_liquidations_1h: number;
  short_liquidations_1h: number;
  avg_liquidations_1h: number;
  momentum_score: number;
  captured_at: string;
};

export type UserProfile = {
  id: number;
  email: string;
  plan: "free" | "pro" | "pro_plus";
  is_active: boolean;
  subscription_status: string | null;
  signal_limit: number | null;
  can_access_all_signals: boolean;
};

export type SubscriptionStatus = {
  provider: string;
  plan: "free" | "pro" | "pro_plus";
  status: string;
  checkout_session_id: string | null;
  stripe_subscription_id: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
};

export type AlertSettings = {
  plan: "free" | "pro" | "pro_plus";
  can_receive_alerts: boolean;
  alerts_globally_enabled: boolean;
  telegram_available: boolean;
  email_available: boolean;
  telegram_enabled: boolean;
  email_enabled: boolean;
  telegram_chat_id: string | null;
  telegram_configured: boolean;
  email: string | null;
  email_configured: boolean;
  min_score: number;
  min_confidence: number;
};

export type ConnectTelegramAlertsPayload = {
  telegram_chat_id: string;
  is_active?: boolean;
};

export type UpdateAlertPreferencesPayload = {
  min_score?: number;
  min_confidence?: number;
  telegram_enabled?: boolean;
  email_enabled?: boolean;
};

export const apiUrl =
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

export const fallbackSignals: Signal[] = [
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

const fallbackSignalFeed: SignalFeed = {
  access_plan: "free",
  total_available: fallbackSignals.length,
  visible_count: 2,
  has_locked_signals: true,
  signals: fallbackSignals.slice(0, 2)
};

const fallbackMarketSnapshots: MarketSnapshot[] = [
  {
    symbol: "BTC",
    name: "Bitcoin",
    category: "Layer 1",
    source: "mock",
    timeframe: "1D",
    open_price: 66171.81,
    high_price: 69500,
    low_price: 61200,
    close_price: 68420.45,
    price_usd: 68420.45,
    change_24h: 3.4,
    volume_24h: 31200000000,
    avg_volume_24h: 16800000000,
    range_high_20d: 69500,
    range_low_20d: 61200,
    funding_rate: 0.009,
    funding_zscore: 1.1,
    open_interest: 14800000000,
    oi_change_24h: 4.2,
    long_liquidations_1h: 8400000,
    short_liquidations_1h: 5200000,
    avg_liquidations_1h: 7500000,
    momentum_score: 84.2,
    captured_at: new Date().toISOString()
  },
  {
    symbol: "ETH",
    name: "Ethereum",
    category: "Layer 1",
    source: "mock",
    timeframe: "1D",
    open_price: 3553.99,
    high_price: 3588,
    low_price: 3010,
    close_price: 3628.18,
    price_usd: 3628.18,
    change_24h: 2.1,
    volume_24h: 18600000000,
    avg_volume_24h: 12800000000,
    range_high_20d: 3588,
    range_low_20d: 3010,
    funding_rate: 0.011,
    funding_zscore: 1.2,
    open_interest: 8200000000,
    oi_change_24h: 3,
    long_liquidations_1h: 6900000,
    short_liquidations_1h: 5100000,
    avg_liquidations_1h: 6200000,
    momentum_score: 79.4,
    captured_at: new Date().toISOString()
  },
  {
    symbol: "SOL",
    name: "Solana",
    category: "Layer 1",
    source: "mock",
    timeframe: "1D",
    open_price: 164.49,
    high_price: 189,
    low_price: 138,
    close_price: 171.89,
    price_usd: 171.89,
    change_24h: 4.5,
    volume_24h: 6200000000,
    avg_volume_24h: 3900000000,
    range_high_20d: 189,
    range_low_20d: 138,
    funding_rate: 0.031,
    funding_zscore: 2.8,
    open_interest: 2400000000,
    oi_change_24h: 11.4,
    long_liquidations_1h: 4100000,
    short_liquidations_1h: 3600000,
    avg_liquidations_1h: 3900000,
    momentum_score: 88.6,
    captured_at: new Date().toISOString()
  }
];

const fallbackAlertSettings: AlertSettings = {
  plan: "free",
  can_receive_alerts: false,
  alerts_globally_enabled: true,
  telegram_available: false,
  email_available: false,
  telegram_enabled: false,
  email_enabled: false,
  telegram_chat_id: null,
  telegram_configured: false,
  email: null,
  email_configured: false,
  min_score: 7,
  min_confidence: 0.6
};

type RequestOptions<T> = {
  token?: string | null;
  method?: string;
  body?: unknown;
  fallback?: T;
};

async function requestJson<T>(path: string, options: RequestOptions<T> = {}): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json"
  };

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  try {
    const response = await fetch(`${apiUrl}${path}`, {
      method: options.method ?? "GET",
      headers,
      cache: "no-store",
      body: options.body ? JSON.stringify(options.body) : undefined
    });

    if (!response.ok) {
      throw new Error(`Request failed for ${path}`);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (options.fallback !== undefined) {
      return options.fallback;
    }
    throw error;
  }
}

export function getAssets(token?: string | null) {
  return requestJson<Asset[]>("/assets", { token, fallback: fallbackAssets });
}

export function getSignals(token?: string | null) {
  return requestJson<Signal[]>("/signals/live", { token, fallback: fallbackSignalFeed.signals });
}

export function getSignalFeed(token?: string | null) {
  return requestJson<SignalFeed>("/signals/feed", { token, fallback: fallbackSignalFeed });
}

export function getMarketSnapshots(token?: string | null) {
  return requestJson<MarketSnapshot[]>("/market/latest", { token, fallback: fallbackMarketSnapshots });
}

export async function getCurrentUser(token?: string | null) {
  if (!token) {
    return null;
  }

  try {
    return await requestJson<UserProfile>("/auth/me", { token });
  } catch {
    return null;
  }
}

export function confirmCheckout(sessionId: string, token: string) {
  return requestJson<SubscriptionStatus>("/billing/confirm", {
    method: "POST",
    token,
    body: { session_id: sessionId }
  });
}

export function getMyAlerts(token?: string | null) {
  if (!token) {
    return Promise.resolve(fallbackAlertSettings);
  }
  return requestJson<AlertSettings>("/alerts/me", {
    token,
    fallback: fallbackAlertSettings
  });
}

async function requestProxyJson<T>(path: string, body?: unknown, method = "POST"): Promise<T> {
  const response = await fetch(path, {
    method,
    headers: {
      "Content-Type": "application/json"
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.detail ?? `Request failed for ${path}`);
  }

  return payload as T;
}

export function connectTelegramAlerts(payload: ConnectTelegramAlertsPayload) {
  return requestProxyJson<AlertSettings>("/api/alerts/telegram/connect", payload);
}

export function updateAlertPreferences(payload: UpdateAlertPreferencesPayload) {
  return requestProxyJson<AlertSettings>("/api/alerts/preferences", payload);
}
