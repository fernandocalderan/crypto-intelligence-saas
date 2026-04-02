import Link from "next/link";

import type { Setup, SetupFeedState, SignalFeed } from "../../lib/api";
import { SetupCard } from "./setup-card";

type SetupsSectionProps = {
  setupState: SetupFeedState;
  accessPlan: SignalFeed["access_plan"];
};

const STATE_PRIORITY: Record<string, number> = {
  EXECUTABLE: 0,
  WATCHLIST: 1,
  WAIT_CONFIRMATION: 2,
  DISCARD: 3
};

function getVisibleSetups(setups: Setup[]) {
  return [...setups]
    .filter((setup) => setup.execution_state !== "DISCARD")
    .sort((left, right) => {
      const stateDelta =
        (STATE_PRIORITY[left.execution_state ?? "WAIT_CONFIRMATION"] ?? 2) -
        (STATE_PRIORITY[right.execution_state ?? "WAIT_CONFIRMATION"] ?? 2);

      if (stateDelta !== 0) {
        return stateDelta;
      }

      if (right.score !== left.score) {
        return right.score - left.score;
      }

      return right.confidence - left.confidence;
    });
}

export function SetupsSection({ setupState, accessPlan }: SetupsSectionProps) {
  const isFreePlan = accessPlan === "free";
  const visibleSetups = getVisibleSetups(setupState.setups);
  const teaserSetups = isFreePlan ? visibleSetups.slice(0, 2) : visibleSetups;

  return (
    <section className="surface p-6 sm:p-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <span className="eyebrow">Setups PRO</span>
          <h2 className="section-title">Confluencias operables con contexto, confirmaciones y plan indicativo.</h2>
          <p className="max-w-3xl text-base leading-7 text-haze">
            Esta es la misma capa comercial que hoy alimenta Telegram: setups por activo con estado operativo claro,
            tesis resumida y plan base. Las señales individuales siguen existiendo debajo, pero aquí se prioriza la
            confluencia útil.
          </p>
        </div>
        <div className="rounded-full border border-white/10 bg-black/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
          {isFreePlan ? "Vista teaser" : `${visibleSetups.length} setups visibles`}
        </div>
      </div>

      {setupState.errorMessage ? (
        <div className="mt-6 rounded-3xl border border-yellow-300/20 bg-yellow-300/10 px-5 py-4 text-sm text-yellow-100">
          {setupState.errorMessage}
        </div>
      ) : null}

      {teaserSetups.length > 0 ? (
        <div className="mt-6 space-y-4">
          {teaserSetups.map((setup) => (
            <SetupCard
              key={`${setup.asset_symbol}-${setup.setup_key}-${setup.generated_at}`}
              setup={setup}
              accessPlan={accessPlan}
            />
          ))}
        </div>
      ) : (
        <div className="mt-6 rounded-3xl border border-white/8 bg-black/10 px-5 py-5 text-sm text-haze">
          No hay setups de confluencia válidos en este momento. El motor sigue evaluando activos y, mientras tanto, las
          señales base quedan visibles más abajo.
        </div>
      )}

      {isFreePlan ? (
        <div className="mt-6 rounded-3xl border border-moss/20 bg-gradient-to-r from-moss/10 via-transparent to-tide/10 p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-ink">Upgrade a Pro</p>
              <p className="max-w-2xl text-sm leading-7 text-haze">
                El plan Free ve solo teaser. Pro y Pro+ desbloquean confirmaciones completas, plan indicativo, warnings
                de calidad y el mismo objeto que ya se envía por Telegram.
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
