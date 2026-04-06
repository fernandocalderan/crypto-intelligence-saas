import { Section } from "../section";

const painPoints = [
  "Señales sin contexto.",
  "Demasiado ruido.",
  "Datos débiles ocultos."
];

export default function ProblemSection() {
  return (
    <Section
      id="problema"
      eyebrow="Problema"
      title="El problema es el ruido."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {painPoints.map((item, index) => (
          <article key={item} className="surface p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tide">Punto {index + 1}</p>
            <p className="mt-3 text-sm leading-6 text-haze">{item}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
