import { Section } from "../section";

const noPoints = [
  "Señales aisladas.",
  "Sin contexto.",
  "Promesas falsas.",
  "Warnings ocultos."
];

const yesPoints = [
  "Setups con confluencia.",
  "Estado operativo.",
  "Confirmaciones claras.",
  "Plan indicativo."
];

export default function BenefitsSection() {
  return (
    <Section
      id="por-que-diferente"
      eyebrow="Por qué es diferente"
      title="Menos ruido. Más estructura."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <article className="surface p-6">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-red-200">No</p>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-haze">
            {noPoints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="surface p-6">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-moss">Sí</p>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-haze">
            {yesPoints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
    </Section>
  );
}
