import { getAssets, getSignals } from "../../lib/api";
import { StatCard } from "../../components/stat-card";

const percentFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1
});

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2
});

export default async function DashboardPage() {
  const [assets, signals] = await Promise.all([getAssets(), getSignals()]);

  const avgScore = signals.length
    ? signals.reduce((sum, signal) => sum + signal.score, 0) / signals.length
    : 0;

  return (
    <div className="space-y-8 py-8">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <span className="eyebrow">Live Mock Dashboard</span>
          <h1 className="section-title">Monitoriza activos, convicción y setup del MVP.</h1>
          <p className="max-w-2xl text-base leading-7 text-haze">
            La página consume el engine de señales en FastAPI y degrada con fallback local si el API no está disponible durante desarrollo.
          </p>
        </div>
      </section>

      <section className="grid gap-5 md:grid-cols-3">
        <StatCard label="Tracked assets" value={String(assets.length)} accent="moss" />
        <StatCard label="Active signals" value={String(signals.length)} accent="tide" />
        <StatCard label="Average score" value={`${percentFormatter.format(avgScore)}/10`} accent="ink" />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="surface p-6 sm:p-8">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-haze">Assets</p>
              <h2 className="mt-2 text-2xl font-semibold text-ink">Universe snapshot</h2>
            </div>
          </div>
          <div className="space-y-4">
            {assets.map((asset) => (
              <div
                key={asset.symbol}
                className="grid gap-3 rounded-3xl border border-white/8 bg-black/10 p-4 sm:grid-cols-[1.2fr_1fr_1fr_1fr]"
              >
                <div>
                  <p className="text-lg font-semibold text-ink">{asset.symbol}</p>
                  <p className="text-sm text-haze">{asset.name}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-haze">Price</p>
                  <p className="mt-1 text-base font-medium text-ink">{currencyFormatter.format(asset.price_usd)}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-haze">24h</p>
                  <p className={`mt-1 text-base font-medium ${asset.change_24h >= 0 ? "text-moss" : "text-red-300"}`}>
                    {asset.change_24h >= 0 ? "+" : ""}
                    {percentFormatter.format(asset.change_24h)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-haze">Momentum</p>
                  <p className="mt-1 text-base font-medium text-ink">{percentFormatter.format(asset.momentum_score)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="surface p-6 sm:p-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-haze">Signals</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink">Scored setups</h2>
          <div className="mt-6 space-y-4">
            {signals.map((signal) => (
              <article key={signal.id} className="rounded-3xl border border-white/8 bg-black/10 p-5">
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
                  {signal.evidence.map((evidence) => (
                    <span
                      key={evidence}
                      className="rounded-full border border-white/10 bg-black/10 px-3 py-1 text-xs text-haze"
                    >
                      {evidence}
                    </span>
                  ))}
                </div>
                <div className="mt-4 flex flex-wrap gap-3 text-xs uppercase tracking-[0.16em] text-haze">
                  <span>Confidence {percentFormatter.format(signal.confidence)}%</span>
                  <span>{new Date(signal.generated_at).toLocaleString()}</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
