import Link from "next/link";

import type { SetupPerformanceState, SignalFeed } from "../../lib/api";

type SetupsPerformanceProps = {
  performanceState: SetupPerformanceState;
  accessPlan: SignalFeed["access_plan"];
  embedded?: boolean;
};

const percentFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1
});

const hourFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1
});

function metricCard(label: string, value: string, muted?: boolean) {
  return (
    <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-haze">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${muted ? "text-haze" : "text-ink"}`}>{value}</p>
    </div>
  );
}

export function SetupsPerformance({ performanceState, accessPlan, embedded = false }: SetupsPerformanceProps) {
  const isFreePlan = accessPlan === "free";
  const isProPlus = accessPlan === "pro_plus";
  const { performance } = performanceState;
  const hasData = performance.total_setups > 0;

  return (
    <section className={embedded ? "" : "surface p-6 sm:p-8"}>
      {!embedded ? (
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <span className="eyebrow">Performance</span>
            <h2 className="section-title">Performance agregada.</h2>
          </div>
          <div className="rounded-full border border-white/10 bg-black/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
            {isFreePlan ? "Vista teaser" : isProPlus ? "Breakdown completo" : "Métricas básicas"}
          </div>
        </div>
      ) : (
        <div className="mb-4 flex items-center justify-between gap-3">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-ink">Performance agregada</p>
          <span className="rounded-full border border-white/10 bg-black/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
            {isFreePlan ? "Vista teaser" : isProPlus ? "Breakdown completo" : "Métricas básicas"}
          </span>
        </div>
      )}

      {performanceState.errorMessage ? (
        <div className="mt-6 rounded-3xl border border-yellow-300/20 bg-yellow-300/10 px-5 py-4 text-sm text-yellow-100">
          {performanceState.errorMessage}
        </div>
      ) : null}

      <div className={`${embedded ? "" : "mt-6"} grid gap-4 md:grid-cols-2 xl:grid-cols-6`}>
        {metricCard("Total setups", isFreePlan ? "Upgrade" : String(performance.total_setups), isFreePlan)}
        {metricCard("Activos", isFreePlan ? "Upgrade" : String(performance.active), isFreePlan)}
        {metricCard("TP1 hit", isFreePlan ? "Upgrade" : `${percentFormatter.format(performance.tp1_hit_pct)}%`, isFreePlan)}
        {metricCard("TP2 hit", isFreePlan ? "Upgrade" : `${percentFormatter.format(performance.tp2_hit_pct)}%`, isFreePlan)}
        {metricCard(
          "Invalidated",
          isFreePlan ? "Upgrade" : `${percentFormatter.format(performance.invalidated_pct)}%`,
          isFreePlan
        )}
        {metricCard(
          "Avg time to TP1",
          isFreePlan ? "Upgrade" : `${hourFormatter.format(performance.avg_time_to_tp1_hours)}h`,
          isFreePlan
        )}
      </div>

      {!hasData && !isFreePlan ? (
        <div className="mt-6 rounded-3xl border border-white/8 bg-black/10 px-5 py-5 text-sm text-haze">
          Aún no hay datos suficientes.
        </div>
      ) : null}

      {isProPlus && performance.by_setup_type.length > 0 ? (
        <div className="mt-6 overflow-hidden rounded-3xl border border-white/8 bg-black/10">
          <div className="grid grid-cols-[1.3fr_0.8fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-white/8 px-4 py-3 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
            <span>Setup type</span>
            <span>Total</span>
            <span>TP1 %</span>
            <span>TP2 %</span>
            <span>Invalidated %</span>
          </div>
          {performance.by_setup_type.map((bucket) => (
            <div
              key={bucket.setup_key}
              className="grid grid-cols-[1.3fr_0.8fr_0.8fr_0.8fr_0.8fr] gap-3 px-4 py-3 text-sm text-haze [&:not(:last-child)]:border-b [&:not(:last-child)]:border-white/8"
            >
              <div>
                <p className="font-medium text-ink">{bucket.setup_type}</p>
                <p className="text-xs uppercase tracking-[0.14em] text-tide">{bucket.setup_key}</p>
              </div>
              <span>{bucket.total}</span>
              <span>{percentFormatter.format(bucket.tp1_hit_pct)}%</span>
              <span>{percentFormatter.format(bucket.tp2_hit_pct)}%</span>
              <span>{percentFormatter.format(bucket.invalidated_pct)}%</span>
            </div>
          ))}
        </div>
      ) : null}

      {isFreePlan && !embedded ? (
        <div className="mt-6 rounded-3xl border border-moss/20 bg-gradient-to-r from-moss/10 via-transparent to-tide/10 p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-ink">Performance premium</p>
              <p className="max-w-2xl text-sm leading-6 text-haze">Pro: métricas básicas. Pro+: breakdown completo.</p>
            </div>
            <Link
              href="/pricing"
              className="inline-flex items-center justify-center rounded-full bg-moss px-6 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d]"
            >
              Ver planes
            </Link>
          </div>
        </div>
      ) : null}
    </section>
  );
}
