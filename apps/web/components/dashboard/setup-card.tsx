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
  const thesisShort = setup.thesis_short ?? setup.summary ?? setup.thesis;
  const summary = setup.summary ?? setup.thesis_short ?? setup.thesis;
  const confluenceLabels =
    setup.signals?.map((signal) => signal.signal_type) ??
    setup.signal_keys?.map((signalKey) => signalKey.replaceAll("_", " ")) ??
    [];

  if (isTeaser) {
    return (
      <article className={`rounded-[2rem] border border-white/8 bg-black/10 ${compact ? "p-5" : "p-6 sm:p-7"}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <p className="text-xl font-semibold text-ink">{setup.asset_symbol}</p>
            <p className="text-sm uppercase tracking-[0.16em] text-tide">{setup.setup_type}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${directionTone(setup.direction)}`}>
              {setup.direction}
            </span>
            {setup.execution_state ? (
              <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${stateTone(setup.execution_state)}`}>
                {setup.execution_state}
              </span>
            ) : null}
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <span className="rounded-full border border-moss/25 bg-moss/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-moss">
            Score {percentFormatter.format(setup.model_score ?? setup.score)}/10
          </span>
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
            Confidence {percentFormatter.format(confidencePct)}%
          </span>
        </div>

        <p className="mt-4 max-w-3xl text-sm leading-7 text-haze">{thesisShort}</p>
      </article>
    );
  }

  return (
    <details className="rounded-[2rem] border border-white/8 bg-black/10 open:border-moss/20">
      <summary className={`cursor-pointer list-none ${compact ? "p-5" : "p-6 sm:p-7"}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-xl font-semibold text-ink">{setup.asset_symbol}</p>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
                {setup.setup_type}
              </span>
            </div>
            <p className="text-sm leading-7 text-haze">{thesisShort}</p>
          </div>

          <div className="flex flex-col items-start gap-2 sm:items-end">
            <div className="flex flex-wrap gap-2">
              <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${directionTone(setup.direction)}`}>
                {setup.direction}
              </span>
              {setup.execution_state ? (
                <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${stateTone(setup.execution_state)}`}>
                  {setup.execution_state}
                </span>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-moss/25 bg-moss/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-moss">
                {percentFormatter.format(setup.model_score ?? setup.score)}/10
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
                {percentFormatter.format(confidencePct)}%
              </span>
            </div>
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-haze">Ver detalle</span>
          </div>
        </div>
      </summary>

      <div className="border-t border-white/8 px-6 pb-6 pt-5 sm:px-7 sm:pb-7">
        <p className="text-sm leading-7 text-haze">{summary}</p>

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

        <div className="mt-5 grid gap-3 lg:grid-cols-3">
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
          </div>
        </div>

        {(setup.data_quality_warnings?.length ?? 0) > 0 ? (
          <div className="mt-5 rounded-3xl border border-yellow-300/20 bg-yellow-300/10 px-4 py-4 text-sm text-yellow-100">
            <p className="font-semibold text-ink">Warnings de calidad</p>
            <ul className="mt-3 space-y-2 leading-6">
              {setup.data_quality_warnings?.slice(0, 3).map((warning) => (
                <li key={`${setup.setup_key}-${warning.code}`}>{warning.message}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </details>
  );
}
