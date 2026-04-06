export type Asset = {
  symbol: string;
  name: string;
  category: string;
  price_usd: number;
  change_24h: number;
  volume_24h: number;
  momentum_score: number;
};

export type ExecutionState = "EXECUTABLE" | "WATCHLIST" | "WAIT_CONFIRMATION" | "DISCARD";

export type SignalConfirmation = {
  label: string;
  severity: "positive" | "warning" | "negative";
};

export type SignalDataQualityWarning = {
  code: string;
  message: string;
  severity: "warning" | "negative";
};

export type SignalKeyData = {
  price?: number | null;
  change_24h?: number | null;
  volume_24h?: number | null;
  funding?: number | null;
  oi_change_24h?: number | null;
  timeframe_base?: string | null;
  source?: string | null;
} | null;

export type SignalActionPlan = {
  action_now: "enter" | "wait" | "discard";
  bias: string;
  trigger_level?: number | null;
  invalidation_level?: number | null;
  tp1?: number | null;
  tp2?: number | null;
  levels_are_indicative?: boolean;
  note?: string | null;
} | null;

export type ProPlusFollowUp = {
  status: string;
  note: string;
} | null;

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
  headline?: string | null;
  execution_state?: ExecutionState | null;
  execution_reason?: string | null;
  summary?: string | null;
  model_score?: number | null;
  confidence_pct?: number | null;
  thesis_short?: string | null;
  key_data?: SignalKeyData;
  confirmations?: SignalConfirmation[];
  action_plan?: SignalActionPlan;
  data_quality_warnings?: SignalDataQualityWarning[];
  is_mock_contaminated?: boolean;
  is_trade_executable?: boolean;
  detail_level?: "teaser" | "full";
  source_snapshot_time?: string | null;
  pro_plus_follow_up?: ProPlusFollowUp;
};

export type SignalFeed = {
  access_plan: "free" | "pro" | "pro_plus";
  total_available: number;
  visible_count: number;
  has_locked_signals: boolean;
  signals: Signal[];
};

export type SetupSignalComponent = {
  signal_key: string;
  signal_type: string;
  direction: "bullish" | "bearish" | "neutral";
  score: number;
  confidence: number;
};

export type Setup = {
  setup_key: string;
  setup_type: string;
  asset_symbol: string;
  direction: "bullish" | "bearish" | "neutral";
  signal_keys: string[];
  signals: SetupSignalComponent[];
  headline: string;
  execution_state?: ExecutionState | null;
  execution_reason?: string | null;
  summary?: string | null;
  thesis: string;
  thesis_short?: string | null;
  score: number;
  confidence: number;
  model_score?: number | null;
  confidence_pct?: number | null;
  key_data?: SignalKeyData;
  confirmations?: SignalConfirmation[];
  action_plan?: SignalActionPlan;
  data_quality_warnings?: SignalDataQualityWarning[];
  is_mock_contaminated?: boolean;
  is_trade_executable?: boolean;
  generated_at: string;
  source_snapshot_time?: string | null;
  detail_level?: "teaser" | "full";
  pro_plus_follow_up?: ProPlusFollowUp;
};

export type SetupFeedState = {
  setups: Setup[];
  source: "api" | "fallback" | "empty";
  errorMessage: string | null;
};

export type SetupHistoryItem = {
  id: string;
  asset_symbol: string;
  setup_key: string;
  setup_type: string;
  headline: string;
  direction: "bullish" | "bearish" | "neutral";
  status: "ACTIVE" | "TP1_HIT" | "TP2_HIT" | "INVALIDATED" | "EXPIRED";
  execution_state: ExecutionState;
  score: number;
  confidence: number;
  summary?: string | null;
  entry?: number | null;
  tp1?: number | null;
  tp2?: number | null;
  invalidation?: number | null;
  current_price?: number | null;
  is_mock_contaminated?: boolean;
  created_at: string;
  updated_at?: string | null;
  detail_level: "teaser" | "full";
};

export type SetupHistoryState = {
  setups: SetupHistoryItem[];
  source: "api" | "fallback" | "empty";
  errorMessage: string | null;
};

export type SetupPerformanceBucket = {
  setup_key: string;
  setup_type: string;
  total: number;
  tp1_hit_pct: number;
  tp2_hit_pct: number;
  invalidated_pct: number;
};

export type SetupPerformance = {
  total_setups: number;
  active: number;
  tp1_hit_pct: number;
  tp2_hit_pct: number;
  invalidated_pct: number;
  avg_time_to_tp1_hours: number;
  by_setup_type: SetupPerformanceBucket[];
};

export type SetupPerformanceState = {
  performance: SetupPerformance;
  source: "api" | "fallback" | "empty";
  errorMessage: string | null;
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
  effective_min_score: number;
  effective_min_confidence_pct: number;
  setup_min_score: number;
  setup_min_confidence_pct: number;
};

export type AlertDeliveryDebugEntry = {
  channel: string;
  delivery_status: string;
  provider_message_id: string | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  sent_at: string | null;
};

export type AlertDebugState = {
  plan: "free" | "pro" | "pro_plus";
  can_receive_alerts: boolean;
  alerts_globally_enabled: boolean;
  telegram_available: boolean;
  bot_configured: boolean;
  telegram_subscription_active: boolean;
  telegram_enabled: boolean;
  telegram_chat_id_present: boolean;
  telegram_chat_id_masked: string | null;
  min_score: number;
  min_confidence: number;
  effective_min_score: number;
  effective_min_confidence_pct: number;
  setup_min_score: number;
  setup_min_confidence_pct: number;
  alerts_process_on_scheduler: boolean;
  recent_deliveries_count: number;
  recent_eligible_signal_count: number;
  latest_sent: AlertDeliveryDebugEntry | null;
  latest_failed: AlertDeliveryDebugEntry | null;
  last_error_code: string | null;
  last_error_known: string | null;
};

export type TelegramConnectInstructions = {
  bot_username: string | null;
  start_command: string;
  steps: string[];
  note: string;
};

export type TelegramTestResult = {
  ok: boolean;
  detail: string;
  telegram_chat_id: string;
  telegram_enabled: boolean;
  provider_message_id: string | null;
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

export const fallbackSetups: Setup[] = [
  {
    setup_key: "trend_continuation",
    setup_type: "Trend Continuation",
    asset_symbol: "BTC",
    direction: "bullish",
    signal_keys: ["volume_spike", "range_breakout"],
    signals: [
      {
        signal_key: "volume_spike",
        signal_type: "Volume Spike",
        direction: "bullish",
        score: 8.8,
        confidence: 83
      },
      {
        signal_key: "range_breakout",
        signal_type: "Range Breakout",
        direction: "bullish",
        score: 8.6,
        confidence: 80
      }
    ],
    headline: "BTC — Trend Continuation",
    execution_state: "EXECUTABLE",
    execution_reason:
      "La confluencia alinea volumen anómalo, ruptura de estructura y niveles indicativos utilizables para una ejecución táctica.",
    summary:
      "BTC alinea volumen anómalo y ruptura de estructura en sesgo bullish. La confluencia ya tiene trigger e invalidación indicativos. Plan base: actuar solo si mantiene la ruptura y respeta la invalidación.",
    thesis:
      "BTC alinea volumen anómalo y ruptura de estructura en sesgo bullish, una combinación típica de continuación táctica cuando el flujo sigue acompañando.",
    thesis_short:
      "BTC alinea volumen anómalo y ruptura de estructura en sesgo bullish, una combinación típica de continuación táctica.",
    score: 8,
    confidence: 82.7,
    model_score: 8,
    confidence_pct: 82.7,
    key_data: {
      price: 68420.45,
      change_24h: 3.4,
      volume_24h: 31200000000,
      funding: 0.009,
      oi_change_24h: 5.2,
      timeframe_base: "1D",
      source: "binance+bybit"
    },
    confirmations: [
      { label: "Volumen anómalo", severity: "positive" },
      { label: "Expansión direccional confirmada", severity: "positive" },
      { label: "Momentum acompaña", severity: "positive" },
      { label: "OI acompaña la tesis", severity: "positive" }
    ],
    action_plan: {
      action_now: "enter",
      bias: "bullish",
      trigger_level: 68557,
      invalidation_level: 67216,
      tp1: 69926,
      tp2: 70952,
      levels_are_indicative: true,
      note:
        "Niveles indicativos del MVP construidos con precio actual, rango 20d y tipo de setup. No son niveles de ejecución automática."
    },
    data_quality_warnings: [
      {
        code: "timeframe_misaligned",
        message: "Los timeframes de las señales base no están perfectamente alineados con el snapshot agregado.",
        severity: "warning"
      }
    ],
    is_mock_contaminated: false,
    is_trade_executable: true,
    generated_at: new Date().toISOString(),
    source_snapshot_time: new Date().toISOString(),
    detail_level: "full",
    pro_plus_follow_up: null
  },
  {
    setup_key: "positioning_trap",
    setup_type: "Positioning Trap",
    asset_symbol: "SOL",
    direction: "bearish",
    signal_keys: ["oi_divergence", "funding_extreme"],
    signals: [
      {
        signal_key: "oi_divergence",
        signal_type: "OI Divergence",
        direction: "bearish",
        score: 7.7,
        confidence: 72
      },
      {
        signal_key: "funding_extreme",
        signal_type: "Funding Extreme",
        direction: "bearish",
        score: 8.2,
        confidence: 76
      }
    ],
    headline: "SOL — Positioning Trap",
    execution_state: "WATCHLIST",
    execution_reason:
      "La estructura es sólida y merece seguimiento, pero todavía no conviene tratarla como entrada inmediata.",
    summary:
      "SOL combina divergencia de OI y exceso de funding en dirección bearish. La tesis es clara, pero conviene esperar mejor activación. Plan base: vigilar trigger e invalidación antes de abrir riesgo.",
    thesis:
      "SOL presenta divergencia entre precio y open interest junto con crowded positioning, una señal de positioning failure que puede terminar en resolución bearish.",
    thesis_short:
      "SOL presenta divergencia entre precio y open interest junto con crowded positioning, una señal de positioning failure.",
    score: 7.6,
    confidence: 74.3,
    model_score: 7.6,
    confidence_pct: 74.3,
    key_data: {
      price: 171.89,
      change_24h: 4.5,
      volume_24h: 6200000000,
      funding: 0.031,
      oi_change_24h: 11.4,
      timeframe_base: "1D",
      source: "mock"
    },
    confirmations: [
      { label: "Divergencia precio/OI visible", severity: "positive" },
      { label: "Funding en extremo", severity: "positive" },
      { label: "Momentum acompaña", severity: "positive" }
    ],
    action_plan: {
      action_now: "wait",
      bias: "bearish",
      trigger_level: 171.37,
      invalidation_level: 177.1,
      tp1: 167.93,
      tp2: 162.21,
      levels_are_indicative: true,
      note:
        "Niveles indicativos del MVP construidos con precio actual, rango 20d y tipo de setup. No son niveles de ejecución automática."
    },
    data_quality_warnings: [
      {
        code: "mock_contamination",
        message: "Parte del contexto usa fallback mock o defaults del MVP. No lo trates como setup fully validated.",
        severity: "negative"
      }
    ],
    is_mock_contaminated: true,
    is_trade_executable: false,
    generated_at: new Date().toISOString(),
    source_snapshot_time: new Date().toISOString(),
    detail_level: "full",
    pro_plus_follow_up: null
  }
];

const fallbackSetupsHistory: SetupHistoryItem[] = [
  {
    id: "hist-btc-trend",
    asset_symbol: "BTC",
    setup_key: "trend_continuation",
    setup_type: "Trend Continuation",
    headline: "BTC — Trend Continuation",
    direction: "bullish",
    status: "TP1_HIT",
    execution_state: "EXECUTABLE",
    score: 8,
    confidence: 82.7,
    summary: "Setup ejecutado con continuación limpia y primer objetivo alcanzado.",
    entry: 68557,
    tp1: 69926,
    tp2: 70952,
    invalidation: 67216,
    current_price: 70124,
    is_mock_contaminated: false,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
    detail_level: "full"
  },
  {
    id: "hist-sol-trap",
    asset_symbol: "SOL",
    setup_key: "positioning_trap",
    setup_type: "Positioning Trap",
    headline: "SOL — Positioning Trap",
    direction: "bearish",
    status: "INVALIDATED",
    execution_state: "EXECUTABLE",
    score: 7.9,
    confidence: 76.1,
    summary: "El setup perdió la estructura y quedó invalidado.",
    entry: 171.37,
    tp1: 167.93,
    tp2: 162.21,
    invalidation: 177.1,
    current_price: 178.4,
    is_mock_contaminated: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 30).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    detail_level: "full"
  }
];

const fallbackSetupsPerformance: SetupPerformance = {
  total_setups: 18,
  active: 4,
  tp1_hit_pct: 44.4,
  tp2_hit_pct: 22.2,
  invalidated_pct: 16.7,
  avg_time_to_tp1_hours: 9.5,
  by_setup_type: [
    {
      setup_key: "trend_continuation",
      setup_type: "Trend Continuation",
      total: 8,
      tp1_hit_pct: 50,
      tp2_hit_pct: 25,
      invalidated_pct: 12.5
    },
    {
      setup_key: "positioning_trap",
      setup_type: "Positioning Trap",
      total: 6,
      tp1_hit_pct: 33.3,
      tp2_hit_pct: 16.7,
      invalidated_pct: 33.3
    },
    {
      setup_key: "squeeze_reversal",
      setup_type: "Squeeze Reversal",
      total: 4,
      tp1_hit_pct: 50,
      tp2_hit_pct: 25,
      invalidated_pct: 0
    }
  ]
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
  min_score: 6.5,
  min_confidence: 0.55,
  effective_min_score: 6.5,
  effective_min_confidence_pct: 55,
  setup_min_score: 6.5,
  setup_min_confidence_pct: 55
};

const fallbackAlertDebug: AlertDebugState = {
  plan: "free",
  can_receive_alerts: false,
  alerts_globally_enabled: true,
  telegram_available: false,
  bot_configured: false,
  telegram_subscription_active: false,
  telegram_enabled: false,
  telegram_chat_id_present: false,
  telegram_chat_id_masked: null,
  min_score: 6.5,
  min_confidence: 0.55,
  effective_min_score: 6.5,
  effective_min_confidence_pct: 55,
  setup_min_score: 6.5,
  setup_min_confidence_pct: 55,
  alerts_process_on_scheduler: true,
  recent_deliveries_count: 0,
  recent_eligible_signal_count: 0,
  latest_sent: null,
  latest_failed: null,
  last_error_code: null,
  last_error_known: null
};

const fallbackTelegramConnectInstructions: TelegramConnectInstructions = {
  bot_username: null,
  start_command: "/start",
  steps: [
    "1. Abre Telegram",
    "2. Busca el bot configurado para este entorno",
    "3. Pulsa Start",
    "4. Pega tu chat ID y vincula tu cuenta"
  ],
  note: "Después de vincular el chat puedes enviar una prueba manual desde el dashboard."
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

export async function getSignalSetups(
  token?: string | null,
  plan: UserProfile["plan"] | SignalFeed["access_plan"] = "free"
): Promise<SetupFeedState> {
  try {
    const setups = await requestJson<Setup[]>("/signals/setups", { token });
    return {
      setups,
      source: "api",
      errorMessage: null
    };
  } catch {
    if (plan === "free") {
      return {
        setups: fallbackSetups.slice(0, 2),
        source: "fallback",
        errorMessage: "Mostrando una vista de ejemplo temporal mientras el backend de setups no responde."
      };
    }

    return {
      setups: [],
      source: "empty",
      errorMessage: "Setups PRO no disponibles temporalmente. Las señales base siguen operativas."
    };
  }
}

export async function getSetupsHistory(
  token?: string | null,
  plan: UserProfile["plan"] | SignalFeed["access_plan"] = "free"
): Promise<SetupHistoryState> {
  try {
    const setups = await requestJson<SetupHistoryItem[]>("/signals/setups/history", { token });
    return {
      setups,
      source: "api",
      errorMessage: null
    };
  } catch {
    if (plan === "free") {
      return {
        setups: fallbackSetupsHistory.slice(0, 2).map((setup) => ({
          ...setup,
          detail_level: "teaser",
          summary: null,
          entry: null,
          tp1: null,
          tp2: null,
          invalidation: null,
          current_price: null
        })),
        source: "fallback",
        errorMessage: "Mostrando una vista de ejemplo del histórico mientras la API no responde."
      };
    }

    return {
      setups: [],
      source: "empty",
      errorMessage: "Histórico de setups no disponible temporalmente."
    };
  }
}

export async function getSetupsPerformance(
  token?: string | null,
  plan: UserProfile["plan"] | SignalFeed["access_plan"] = "free"
): Promise<SetupPerformanceState> {
  try {
    const performance = await requestJson<SetupPerformance>("/signals/setups/performance", { token });
    return {
      performance,
      source: "api",
      errorMessage: null
    };
  } catch {
    if (plan === "free") {
      return {
        performance: { ...fallbackSetupsPerformance, by_setup_type: [] },
        source: "fallback",
        errorMessage: "Mostrando una vista teaser de performance mientras la API no responde."
      };
    }

    return {
      performance: {
        total_setups: 0,
        active: 0,
        tp1_hit_pct: 0,
        tp2_hit_pct: 0,
        invalidated_pct: 0,
        avg_time_to_tp1_hours: 0,
        by_setup_type: []
      },
      source: "empty",
      errorMessage: "Métricas de performance no disponibles temporalmente."
    };
  }
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

export function getMyAlertsDebug(token?: string | null) {
  if (!token) {
    return Promise.resolve(fallbackAlertDebug);
  }
  return requestJson<AlertDebugState>("/alerts/debug/me", {
    token,
    fallback: fallbackAlertDebug
  });
}

export function getTelegramConnectInstructions(token?: string | null) {
  if (!token) {
    return Promise.resolve(fallbackTelegramConnectInstructions);
  }
  return requestJson<TelegramConnectInstructions>("/alerts/telegram/connect-instructions", {
    token,
    fallback: fallbackTelegramConnectInstructions
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
  const raw = await response.text();
  const payload = raw ? JSON.parse(raw) : {};

  if (!response.ok) {
    throw new Error(payload.detail ?? payload.message ?? `Request failed for ${path}`);
  }

  return payload as T;
}

export function connectTelegramAlerts(payload: ConnectTelegramAlertsPayload) {
  return requestProxyJson<AlertSettings>("/api/alerts/telegram/connect", payload);
}

export function updateAlertPreferences(payload: UpdateAlertPreferencesPayload) {
  return requestProxyJson<AlertSettings>("/api/alerts/preferences", payload);
}

export function sendTelegramTest() {
  return requestProxyJson<TelegramTestResult>("/api/alerts/telegram/test");
}

export function revalidateTelegramDebug() {
  return requestProxyJson<AlertDebugState>("/api/alerts/debug/me", undefined, "GET");
}
