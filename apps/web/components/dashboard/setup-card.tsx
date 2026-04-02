import type { Setup } from "../../lib/api";

type SetupCardProps = {
  setup: Setup;
  accessPlan: "free" | "pro" | "pro_plus";
  compact?: boolean;
};

const percentFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1
});

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2
});

const compactCurrencyFormatter = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1
});

const fundingFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 4,
  maximumFractionDigits: 4
});

function stateTone(state?: Setup["execution_state"]) {
  if (state === "EXECUTABLE") {
    return "border-moss/30 bg-moss/10 text-moss";
  }
  if (state === "WATCHLIST") {
    return "border-yellow-300/25 bg-yellow-300/10 text-yellow-100";
  }
  if (state === "WAIT_CONFIRMATION") {
    return "border-orange-300/25 bg-orange-300/10 text-orange-100";
  }
  return "border-red-300/25 bg-red-300/10 text-red-100";
}

function directionTone(direction?: Setup["direction"]) {
  if (direction === "bullish") {
    return "border-moss/30 bg-moss/10 text-moss";
  }
  if (direction === "bearish") {
    return "border-red-300/30 bg-red-300/10 text-red-200";
  }
  return "border-white/10 bg-white/5 text-haze";
}

function confirmationTone(severity: "positive" | "warning" | "negative") {
  if (severity === "positive") {
    return "border-moss/20 bg-moss/10 text-moss";
  }
  if (severity === "negative") {
    return "border-red-300/20 bg-red-300/10 text-red-100";
  }
  return "border-yellow-300/20 bg-yellow-300/10 text-yellow-100";
}

function formatLevel(value?: number | null) {
  if (value === null || value === undefined) {
    return "n/d";
  }
  return currencyFormatter.format(value);
}

export function SetupCard({ setup, accessPlan, compact = false }: SetupCardProps) {
  const isTeaser = accessPlan === "free" || setup.detail_level === "teaser";
  const confidencePct = setup.confidence_pct ?? setup.confidence;
  const headline = setup.headline ?? `${setup.asset_symbol} — ${setup.setup_type}`;
  const summary = setup.summary ?? setup.thesis_short ?? setup.thesis;
  const confluenceLabels =
    setup.signals?.map((signal) => signal.signal_type) ??
    setup.signal_keys?.map((signalKey) => signalKey.replaceAll("_", " ")) ??
    [];

  if (isTeaser) {
    return (
      <article className={`rounded-3xl border border-white/8 bg-black/10 ${compact ? "p-4" : "p-5"}`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-lg font-semibold text-ink">{headline}</p>
            <p className="text-sm uppercase tracking-[0.14em] text-tide">
              {setup.setup_type} · {setup.direction}
            </p>
          </div>
          <div className="rounded-full border border-moss/25 bg-moss/10 px-3 py-1 text-sm font-semibold text-moss">
            Score {percentFormatter.format(setup.model_score ?? setup.score)}/10
          </div>
        </div>

        <p className="mt-4 text-sm leading-7 text-haze">{setup.thesis_short ?? setup.thesis}</p>

        <div className="mt-4 flex flex-wrap gap-2">
          {confluenceLabels.slice(0, 2).map((label) => (
            <span
              key={`${setup.setup_key}-${label}`}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze"
            >
              {label}
            </span>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${directionTone(setup.direction)}`}>
            {setup.direction}
          </span>
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
            Confidence {percentFormatter.format(confidencePct)}%
          </span>
          <span className="rounded-full border border-yellow-300/20 bg-yellow-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-yellow-100">
            Upgrade para ver plan
          </span>
        </div>
      </article>
    );
  }

  return (
    <article className={`rounded-3xl border border-white/8 bg-black/10 ${compact ? "p-4" : "p-5"}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-lg font-semibold text-ink">{headline}</p>
          <p className="text-sm uppercase tracking-[0.14em] text-tide">
            {setup.setup_type} · {setup.direction} · {setup.key_data?.source ?? "runtime"}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {setup.execution_state ? (
            <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${stateTone(setup.execution_state)}`}>
              {setup.execution_state}
            </span>
          ) : null}
          <span className="rounded-full border border-moss/25 bg-moss/10 px-3 py-1 text-sm font-semibold text-moss">
            Score {percentFormatter.format(setup.model_score ?? setup.score)}/10
          </span>
          {setup.is_trade_executable ? (
            <span className="rounded-full border border-moss/25 bg-moss/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-moss">
              Trade ready
            </span>
          ) : null}
        </div>
      </div>

      <p className="mt-4 text-sm leading-7 text-haze">{summary}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {confluenceLabels.map((label) => (
          <span
            key={`${setup.setup_key}-${label}`}
            className="rounded-full border border-tide/20 bg-tide/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-ink"
          >
            {label}
          </span>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${directionTone(setup.direction)}`}>
          {setup.direction}
        </span>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
          Confidence {percentFormatter.format(confidencePct)}%
        </span>
        {setup.action_plan ? (
          <span className="rounded-full border border-white/10 bg-black/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
            Action now: {setup.action_plan.action_now}
          </span>
        ) : null}
        {setup.is_mock_contaminated ? (
          <span className="rounded-full border border-red-300/25 bg-red-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-red-100">
            Mock contamination
          </span>
        ) : null}
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
          <p className="font-semibold text-ink">Datos clave</p>
          <ul className="mt-3 space-y-2 leading-6">
            <li>Precio: {setup.key_data?.price ? currencyFormatter.format(setup.key_data.price) : "n/d"}</li>
            <li>
              24h:{" "}
              {setup.key_data?.change_24h !== undefined && setup.key_data?.change_24h !== null
                ? `${setup.key_data.change_24h >= 0 ? "+" : ""}${percentFormatter.format(setup.key_data.change_24h)}%`
                : "n/d"}
            </li>
            <li>Volumen: {setup.key_data?.volume_24h ? compactCurrencyFormatter.format(setup.key_data.volume_24h) : "n/d"}</li>
            <li>
              Funding:{" "}
              {setup.key_data?.funding !== undefined && setup.key_data?.funding !== null
                ? fundingFormatter.format(setup.key_data.funding)
                : "n/d"}
            </li>
            <li>
              OI:{" "}
              {setup.key_data?.oi_change_24h !== undefined && setup.key_data?.oi_change_24h !== null
                ? `${setup.key_data.oi_change_24h >= 0 ? "+" : ""}${percentFormatter.format(setup.key_data.oi_change_24h)}%`
                : "n/d"}
            </li>
            <li>
              Base: {setup.key_data?.timeframe_base ?? "n/d"} · {setup.key_data?.source ?? "n/d"}
            </li>
          </ul>
        </div>

        <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
          <p className="font-semibold text-ink">Confirmaciones</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(setup.confirmations ?? []).slice(0, 4).map((confirmation) => (
              <span
                key={`${setup.setup_key}-${confirmation.label}`}
                className={`rounded-full border px-3 py-1 text-xs ${confirmationTone(confirmation.severity)}`}
              >
                {confirmation.label}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
          <p className="font-semibold text-ink">Plan indicativo</p>
          <ul className="mt-3 space-y-2 leading-6">
            <li>Bias: {setup.action_plan?.bias ?? setup.direction}</li>
            <li>Trigger: {formatLevel(setup.action_plan?.trigger_level)}</li>
            <li>Invalidación: {formatLevel(setup.action_plan?.invalidation_level)}</li>
            <li>TP1: {formatLevel(setup.action_plan?.tp1)}</li>
            <li>TP2: {formatLevel(setup.action_plan?.tp2)}</li>
          </ul>
          {setup.action_plan?.note ? <p className="mt-3 text-xs text-haze">{setup.action_plan.note}</p> : null}
        </div>
      </div>

      {(setup.data_quality_warnings?.length ?? 0) > 0 ? (
        <div className="mt-5 rounded-3xl border border-yellow-300/20 bg-yellow-300/10 px-4 py-4 text-sm text-yellow-100">
          <p className="font-semibold text-ink">Riesgo / calidad del dato</p>
          <ul className="mt-3 space-y-2 leading-6">
            {setup.data_quality_warnings?.slice(0, 3).map((warning) => (
              <li key={`${setup.setup_key}-${warning.code}`}>{warning.message}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {accessPlan === "pro_plus" && setup.pro_plus_follow_up ? (
        <div className="mt-5 rounded-3xl border border-tide/20 bg-tide/10 px-4 py-4 text-sm text-ink">
          <p className="font-semibold">Hook Pro+</p>
          <p className="mt-2">{setup.pro_plus_follow_up.note}</p>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-3 text-xs uppercase tracking-[0.16em] text-haze">
        <span>{new Date(setup.generated_at).toLocaleString()}</span>
        {setup.execution_reason ? <span>{setup.execution_reason}</span> : null}
      </div>
    </article>
  );
}
