import { fallbackSetups } from "../../lib/api";
import { SetupCard } from "../dashboard/setup-card";
import { Section } from "../section";

const deliveryPoints = [
  "Activo y dirección.",
  "Estado operativo.",
  "Confirmaciones clave.",
  "Plan indicativo."
];

export default function AlertExampleSection() {
  return (
    <Section
      id="ejemplo-setup"
      eyebrow="Ejemplo de Setup"
      title="Así se ve un setup."
    >
      <div className="grid gap-5 lg:grid-cols-[0.82fr_1.18fr]">
        <article className="surface p-6">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tide">Qué resume en segundos</p>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-haze">
            {deliveryPoints.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </article>
        <SetupCard setup={fallbackSetups[0]} accessPlan="pro" />
      </div>
    </Section>
  );
}
