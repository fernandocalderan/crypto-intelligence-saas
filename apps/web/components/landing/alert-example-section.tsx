import { SignalCard } from "../signal-card";
import { Section } from "../section";
import { fallbackSignals } from "../../lib/api";

export default function AlertExampleSection() {
  return (
    <Section
      id="ejemplo-alerta"
      eyebrow="Ejemplo alerta"
      title="Qué ve el usuario cuando aparece una oportunidad."
      description="Una alerta útil no solo dice qué activo se mueve. También resume tesis, score y evidencia mínima para justificar atención."
    >
      <div className="grid gap-5 lg:grid-cols-[0.85fr_1.15fr]">
        <article className="surface p-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tide">Formato</p>
          <ul className="mt-5 space-y-4 text-base leading-7 text-haze">
            <li>Dirección de la señal y timeframe.</li>
            <li>Score visible para priorizar setups rápidamente.</li>
            <li>Tesis corta y evidencia legible sin jerga innecesaria.</li>
          </ul>
        </article>
        <SignalCard signal={fallbackSignals[0]} />
      </div>
    </Section>
  );
}
