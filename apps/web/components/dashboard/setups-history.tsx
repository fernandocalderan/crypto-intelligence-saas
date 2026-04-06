import Link from "next/link";

import type { SetupHistoryItem, SetupHistoryState, SetupPerformanceState, SignalFeed } from "../../lib/api";
import { SetupsPerformance } from "./setups-performance";

type SetupsHistoryProps = {
  historyState: SetupHistoryState;
  performanceState: SetupPerformanceState;
  accessPlan: SignalFeed["access_plan"];
};

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2
});

const percentFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1
});

function statusTone(status: SetupHistoryItem["status"]) {
  if (status === "TP2_HIT") {
    return "border-moss/30 bg-moss/10 text-moss";
  }
  if (status === "TP1_HIT") {
    return "border-tide/30 bg-tide/10 text-ink";
  }
  if (status === "ACTIVE") {
    return "border-yellow-300/25 bg-yellow-300/10 text-yellow-100";
  }
  if (status === "EXPIRED") {
    return "border-white/10 bg-white/5 text-haze";
  }
  return "border-red-300/25 bg-red-300/10 text-red-100";
}

function directionTone(direction: SetupHistoryItem["direction"]) {
  if (direction === "bullish") {
    return "border-moss/30 bg-moss/10 text-moss";
  }
  if (direction === "bearish") {
    return "border-red-300/30 bg-red-300/10 text-red-200";
  }
  return "border-white/10 bg-white/5 text-haze";
}

function formatLevel(value?: number | null) {
  if (value === null || value === undefined) {
    return "n/d";
  }
  return currencyFormatter.format(value);
}

export function SetupsHistory({ historyState, performanceState, accessPlan }: SetupsHistoryProps) {
  const isFreePlan = accessPlan === "free";
  const visibleItems = isFreePlan ? historyState.setups.slice(0, 2) : historyState.setups;

  return (
    <details className="surface p-6 sm:p-8">
      <summary className="cursor-pointer list-none">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <span className="eyebrow">Histórico de Setups</span>
            <h2 className="section-title">Histórico y performance.</h2>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="rounded-full border border-white/10 bg-black/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
              {isFreePlan ? "Vista teaser" : `${visibleItems.length} registros`}
            </div>
            <div className="rounded-full border border-white/10 bg-black/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-ink">
              Abrir
            </div>
          </div>
        </div>
      </summary>

      <div className="mt-6 space-y-6 border-t border-white/8 pt-6">
        <SetupsPerformance performanceState={performanceState} accessPlan={accessPlan} embedded />

        {historyState.errorMessage ? (
          <div className="rounded-3xl border border-yellow-300/20 bg-yellow-300/10 px-5 py-4 text-sm text-yellow-100">
            {historyState.errorMessage}
          </div>
        ) : null}

        {visibleItems.length > 0 ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {visibleItems.map((setup) => (
              <article key={setup.id} className="rounded-3xl border border-white/8 bg-black/10 p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold text-ink">{setup.headline}</p>
                    <p className="text-sm uppercase tracking-[0.14em] text-tide">
                      {setup.setup_type} · {setup.direction}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${statusTone(setup.status)}`}>
                      {setup.status}
                    </span>
                    <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${directionTone(setup.direction)}`}>
                      {setup.direction}
                    </span>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="rounded-full border border-moss/25 bg-moss/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-moss">
                    Score {percentFormatter.format(setup.score)}/10
                  </span>
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
                    Confidence {percentFormatter.format(setup.confidence)}%
                  </span>
                  {setup.is_mock_contaminated ? (
                    <span className="rounded-full border border-red-300/25 bg-red-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-red-100">
                      Mock contamination
                    </span>
                  ) : null}
                </div>

                {setup.detail_level === "full" && setup.summary ? (
                  <p className="mt-4 text-sm leading-6 text-haze">{setup.summary}</p>
                ) : (
                  <p className="mt-4 text-sm leading-6 text-haze">{setup.asset_symbol} en histórico reciente.</p>
                )}

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
                    <p className="font-semibold text-ink">Lifecycle</p>
                    <ul className="mt-3 space-y-2 leading-6">
                      <li>Creado: {new Date(setup.created_at).toLocaleString()}</li>
                      <li>Actualizado: {setup.updated_at ? new Date(setup.updated_at).toLocaleString() : "n/d"}</li>
                      <li>Estado: {setup.status}</li>
                      <li>Estado operativo: {setup.execution_state}</li>
                    </ul>
                  </div>

                  <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
                    <p className="font-semibold text-ink">Niveles</p>
                    <ul className="mt-3 space-y-2 leading-6">
                      <li>Entry: {setup.detail_level === "full" ? formatLevel(setup.entry) : "Upgrade para ver"}</li>
                      <li>TP1: {setup.detail_level === "full" ? formatLevel(setup.tp1) : "Upgrade para ver"}</li>
                      <li>TP2: {setup.detail_level === "full" ? formatLevel(setup.tp2) : "Upgrade para ver"}</li>
                      <li>
                        Invalidación: {setup.detail_level === "full" ? formatLevel(setup.invalidation) : "Upgrade para ver"}
                      </li>
                      <li>
                        Precio actual: {setup.detail_level === "full" ? formatLevel(setup.current_price) : "Upgrade para ver"}
                      </li>
                    </ul>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border border-white/8 bg-black/10 px-5 py-5 text-sm text-haze">
            Aún no hay setups en histórico.
          </div>
        )}

        {isFreePlan ? (
          <div className="rounded-3xl border border-moss/20 bg-gradient-to-r from-moss/10 via-transparent to-tide/10 p-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-ink">Tracking premium</p>
              <p className="max-w-2xl text-sm leading-6 text-haze">Pro desbloquea niveles y lifecycle.</p>
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
      </div>
    </details>
  );
}
