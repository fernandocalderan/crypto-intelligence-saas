import type { Signal, SignalFeed } from "../lib/api";

type SignalCardProps = {
  signal?: Signal;
  locked?: boolean;
  compact?: boolean;
  accessPlan?: SignalFeed["access_plan"];
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

function stateTone(state?: Signal["execution_state"]) {
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

function directionTone(direction?: Signal["direction"]) {
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

export function SignalCard({ signal, locked = false, compact = false, accessPlan = "free" }: SignalCardProps) {
  if (locked || !signal) {
    return (
      <article className="rounded-3xl border border-white/8 bg-black/10 p-5 opacity-80">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-lg font-semibold text-ink">Señal bloqueada</p>
            <p className="text-sm uppercase tracking-[0.14em] text-haze">Disponible en Pro o Pro+</p>
          </div>
          <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
            Upgrade
          </div>
        </div>
        <p className="mt-4 text-sm leading-7 text-haze">
          El plan Free ve una parte del feed. El upgrade desbloquea setups con confirmaciones, plan y warnings de calidad del dato.
        </p>
      </article>
    );
  }

  const isTeaser = accessPlan === "free" || signal.detail_level === "teaser";
  const confidencePct = signal.confidence_pct ?? signal.confidence;
  const headline = signal.headline ?? `${signal.asset_symbol} — ${signal.signal_type}`;
  const summary = signal.summary ?? signal.thesis_short ?? signal.thesis;
  const actionPlan = signal.action_plan;
  const keyData = signal.key_data;

  if (isTeaser) {
    return (
      <article className={`rounded-3xl border border-white/8 bg-black/10 ${compact ? "p-4" : "p-5"}`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-lg font-semibold text-ink">{headline}</p>
            <p className="text-sm uppercase tracking-[0.14em] text-tide">
              {signal.direction} · {signal.timeframe}
            </p>
          </div>
          <div className="rounded-full border border-moss/25 bg-moss/10 px-3 py-1 text-sm font-semibold text-moss">
            Score {percentFormatter.format(signal.model_score ?? signal.score)}/10
          </div>
        </div>
        <p className="mt-4 text-sm leading-7 text-haze">{signal.thesis_short ?? signal.thesis}</p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${directionTone(signal.direction)}`}>
            {signal.direction}
          </span>
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
            {percentFormatter.format(confidencePct)}% confidence
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
            {signal.timeframe} · {signal.source}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {signal.execution_state ? (
            <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${stateTone(signal.execution_state)}`}>
              {signal.execution_state}
            </span>
          ) : null}
          <div className="rounded-full border border-moss/25 bg-moss/10 px-3 py-1 text-sm font-semibold text-moss">
            Score {percentFormatter.format(signal.model_score ?? signal.score)}/10
          </div>
        </div>
      </div>

      <p className="mt-4 text-sm leading-7 text-haze">{summary}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${directionTone(signal.direction)}`}>
          {signal.direction}
        </span>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
          Confidence {percentFormatter.format(confidencePct)}%
        </span>
        {actionPlan ? (
          <span className="rounded-full border border-white/10 bg-black/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
            Action now: {actionPlan.action_now}
          </span>
        ) : null}
      </div>

      {keyData ? (
        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
            <p className="font-semibold text-ink">Datos clave</p>
            <ul className="mt-3 space-y-2 leading-6">
              <li>Precio: {keyData.price ? currencyFormatter.format(keyData.price) : "n/d"}</li>
              <li>24h: {keyData.change_24h !== undefined && keyData.change_24h !== null ? `${keyData.change_24h >= 0 ? "+" : ""}${percentFormatter.format(keyData.change_24h)}%` : "n/d"}</li>
              <li>Volumen: {keyData.volume_24h ? compactCurrencyFormatter.format(keyData.volume_24h) : "n/d"}</li>
              <li>Funding: {keyData.funding !== undefined && keyData.funding !== null ? fundingFormatter.format(keyData.funding) : "n/d"}</li>
              <li>OI: {keyData.oi_change_24h !== undefined && keyData.oi_change_24h !== null ? `${keyData.oi_change_24h >= 0 ? "+" : ""}${percentFormatter.format(keyData.oi_change_24h)}%` : "n/d"}</li>
              <li>Base: {keyData.timeframe_base ?? "n/d"} · {keyData.source ?? "n/d"}</li>
            </ul>
          </div>

          <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
            <p className="font-semibold text-ink">Confirmaciones</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {(signal.confirmations ?? []).map((confirmation) => (
                <span
                  key={`${signal.id}-${confirmation.label}`}
                  className={`rounded-full border px-3 py-1 text-xs ${confirmationTone(confirmation.severity)}`}
                >
                  {confirmation.label}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
            <p className="font-semibold text-ink">Plan de acción</p>
            <ul className="mt-3 space-y-2 leading-6">
              <li>Bias: {actionPlan?.bias ?? signal.direction}</li>
              <li>Trigger: {formatLevel(actionPlan?.trigger_level)}</li>
              <li>Invalidación: {formatLevel(actionPlan?.invalidation_level)}</li>
              <li>TP1: {formatLevel(actionPlan?.tp1)}</li>
              <li>TP2: {formatLevel(actionPlan?.tp2)}</li>
            </ul>
            {actionPlan?.note ? <p className="mt-3 text-xs text-haze">{actionPlan.note}</p> : null}
          </div>
        </div>
      ) : null}

      {(signal.data_quality_warnings?.length ?? 0) > 0 ? (
        <div className="mt-5 rounded-3xl border border-yellow-300/20 bg-yellow-300/10 px-4 py-4 text-sm text-yellow-100">
          <p className="font-semibold text-ink">Riesgo / calidad del dato</p>
          <ul className="mt-3 space-y-2 leading-6">
            {signal.data_quality_warnings?.map((warning) => (
              <li key={`${signal.id}-${warning.code}`}>{warning.message}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {accessPlan === "pro_plus" && signal.pro_plus_follow_up ? (
        <div className="mt-5 rounded-3xl border border-tide/20 bg-tide/10 px-4 py-4 text-sm text-ink">
          <p className="font-semibold">Hook Pro+</p>
          <p className="mt-2">{signal.pro_plus_follow_up.note}</p>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-3 text-xs uppercase tracking-[0.16em] text-haze">
        <span>{new Date(signal.generated_at).toLocaleString()}</span>
        {signal.execution_reason ? <span>{signal.execution_reason}</span> : null}
      </div>
    </article>
  );
}
