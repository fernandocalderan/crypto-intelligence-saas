import Link from "next/link";

import type { SetupHistoryItem, SetupHistoryState, SignalFeed } from "../../lib/api";

type SetupsHistoryProps = {
  historyState: SetupHistoryState;
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

export function SetupsHistory({ historyState, accessPlan }: SetupsHistoryProps) {
  const isFreePlan = accessPlan === "free";
  const visibleItems = isFreePlan ? historyState.setups.slice(0, 2) : historyState.setups;

  return (
    <section className="surface p-6 sm:p-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <span className="eyebrow">Histórico de Setups</span>
          <h2 className="section-title">Lifecycle de setups activos, cerrados e invalidados.</h2>
          <p className="max-w-3xl text-base leading-7 text-haze">
            Este bloque da contexto de evolución: qué setups siguen activos, cuáles llegaron a objetivos y cuáles
            quedaron invalidados o expiraron. Es la base para tracking y performance del producto premium.
          </p>
        </div>
        <div className="rounded-full border border-white/10 bg-black/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
          {isFreePlan ? "Vista teaser" : `${visibleItems.length} registros`}
        </div>
      </div>

      {historyState.errorMessage ? (
        <div className="mt-6 rounded-3xl border border-yellow-300/20 bg-yellow-300/10 px-5 py-4 text-sm text-yellow-100">
          {historyState.errorMessage}
        </div>
      ) : null}

      {visibleItems.length > 0 ? (
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
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
                <p className="mt-4 text-sm leading-7 text-haze">{setup.summary}</p>
              ) : (
                <p className="mt-4 text-sm leading-7 text-haze">
                  {setup.asset_symbol} mantiene un registro histórico dentro del lifecycle premium del producto.
                </p>
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
        <div className="mt-6 rounded-3xl border border-white/8 bg-black/10 px-5 py-5 text-sm text-haze">
          Todavía no hay setups persistidos en el histórico. En cuanto el scheduler detecte setups ejecutables y luego
          evolucionen, aparecerán aquí con su lifecycle.
        </div>
      )}

      {isFreePlan ? (
        <div className="mt-6 rounded-3xl border border-moss/20 bg-gradient-to-r from-moss/10 via-transparent to-tide/10 p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-ink">Tracking premium</p>
              <p className="max-w-2xl text-sm leading-7 text-haze">
                Pro y Pro+ desbloquean entry, objetivos, invalidación y seguimiento del lifecycle completo de cada
                setup persistido.
              </p>
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
