import { fallbackSetups } from "../../lib/api";
import { SetupCard } from "../dashboard/setup-card";
import { Section } from "../section";

const deliveryPoints = [
  "Activo, dirección y tipo de setup visibles al instante.",
  "Estado operativo para distinguir entre ejecución, watchlist y espera.",
  "Confirmaciones y warnings de calidad para evitar lecturas demasiado optimistas.",
  "Plan indicativo con trigger, invalidación y objetivos cuando el contexto lo permite."
];

export default function AlertExampleSection() {
  return (
    <Section
      id="ejemplo-setup"
      eyebrow="Ejemplo de Setup"
      title="Lo que ves no es una alerta cruda. Es una lectura operativa resumida."
      description="Telegram y dashboard hablan el mismo idioma: confluencia, resumen, estado operativo y plan indicativo en el mismo objeto comercial."
    >
      <div className="grid gap-5 lg:grid-cols-[0.82fr_1.18fr]">
        <article className="surface p-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tide">Qué resume en segundos</p>
          <ul className="mt-5 space-y-4 text-base leading-7 text-haze">
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
