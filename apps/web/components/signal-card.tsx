import type { Signal } from "../lib/api";

type SignalCardProps = {
  signal?: Signal;
  locked?: boolean;
  compact?: boolean;
};

const percentFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1
});

export function SignalCard({ signal, locked = false, compact = false }: SignalCardProps) {
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
          El plan Free ve una parte del feed. El upgrade desbloquea el resto de setups activos con su contexto completo.
        </p>
      </article>
    );
  }

  return (
    <article className={`rounded-3xl border border-white/8 bg-black/10 ${compact ? "p-4" : "p-5"}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-lg font-semibold text-ink">{signal.asset_symbol}</p>
          <p className="text-sm uppercase tracking-[0.14em] text-tide">
            {signal.signal_type} · {signal.timeframe}
          </p>
        </div>
        <div className="rounded-full border border-moss/25 bg-moss/10 px-3 py-1 text-sm font-semibold text-moss">
          Score {percentFormatter.format(signal.score)}/10
        </div>
      </div>
      <p className="mt-4 text-sm leading-7 text-haze">{signal.thesis}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <span
          className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${
            signal.direction === "bullish"
              ? "border-moss/30 bg-moss/10 text-moss"
              : "border-red-300/30 bg-red-300/10 text-red-200"
          }`}
        >
          {signal.direction}
        </span>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
          {signal.source}
        </span>
        {signal.evidence.slice(0, compact ? 2 : 3).map((evidence) => (
          <span key={evidence} className="rounded-full border border-white/10 bg-black/10 px-3 py-1 text-xs text-haze">
            {evidence}
          </span>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-3 text-xs uppercase tracking-[0.16em] text-haze">
        <span>Confidence {percentFormatter.format(signal.confidence)}%</span>
        <span>{new Date(signal.generated_at).toLocaleString()}</span>
      </div>
    </article>
  );
}
