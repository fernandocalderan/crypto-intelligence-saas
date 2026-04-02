"use client";

import { useRouter } from "next/navigation";

import { trackEvent } from "../lib/tracking";

type UpgradeBannerProps = {
  hiddenSignals: number;
};

export function UpgradeBanner({ hiddenSignals }: UpgradeBannerProps) {
  const router = useRouter();

  function handleUpgrade() {
    trackEvent({
      event: "upgrade_banner_clicked",
      context: "dashboard",
      properties: {
        hidden_signals: hiddenSignals
      }
    });
    router.push("/pricing");
  }

  return (
    <section className="surface border-moss/20 bg-gradient-to-r from-moss/10 via-transparent to-tide/10 p-6 sm:p-8">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-3">
          <span className="eyebrow">Upgrade</span>
          <h2 className="section-title">El plan Free deja parte del feed bloqueado.</h2>
          <p className="max-w-2xl text-base leading-7 text-haze">
            Ahora mismo estás viendo una muestra. Hay {hiddenSignals} señal{hiddenSignals === 1 ? "" : "es"} más
            disponibles para planes Pro y Pro+.
          </p>
        </div>
        <button
          type="button"
          onClick={handleUpgrade}
          className="rounded-full bg-moss px-6 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d]"
        >
          Ver planes
        </button>
      </div>
    </section>
  );
}
