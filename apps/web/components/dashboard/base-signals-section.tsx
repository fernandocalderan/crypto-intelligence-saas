import { SignalCard } from "../signal-card";
import type { Signal, SignalFeed } from "../../lib/api";

type BaseSignalsSectionProps = {
  signals: Signal[];
  accessPlan: SignalFeed["access_plan"];
  lockedPreviewCount?: number;
};

export function BaseSignalsSection({
  signals,
  accessPlan,
  lockedPreviewCount = 0
}: BaseSignalsSectionProps) {
  return (
    <details className="surface p-6 sm:p-8">
      <summary className="cursor-pointer list-none">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <span className="eyebrow">Señales base</span>
            <h2 className="section-title">Capa técnica secundaria.</h2>
            <p className="max-w-3xl text-sm leading-6 text-haze">Inspección técnica, no decisión principal.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="rounded-full border border-white/10 bg-black/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-haze">
              {signals.length + lockedPreviewCount} elementos
            </div>
            <div className="rounded-full border border-white/10 bg-black/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-ink">
              Abrir
            </div>
          </div>
        </div>
      </summary>

      <div className="mt-6 space-y-4 border-t border-white/8 pt-6">
        {signals.map((signal) => (
          <SignalCard key={signal.id} signal={signal} accessPlan={accessPlan} compact />
        ))}
        {Array.from({ length: lockedPreviewCount }).map((_, index) => (
          <SignalCard key={`locked-${index}`} locked compact />
        ))}
      </div>
    </details>
  );
}
