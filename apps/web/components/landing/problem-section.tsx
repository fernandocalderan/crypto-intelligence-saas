import { Section } from "../section";

const painPoints = [
  "El mercado genera demasiadas alertas sin jerarquía ni contexto útil para decidir.",
  "Muchos dashboards enseñan precio, pero no explican por qué una señal merece atención.",
  "Monetizar inteligencia crypto falla cuando el usuario no entiende qué está pagando exactamente."
];

export default function ProblemSection() {
  return (
    <Section
      id="problema"
      eyebrow="Problema"
      title="Un trader no paga por más ruido. Paga por un mejor filtro."
      description="La fricción no suele estar en conseguir datos. Está en ordenarlos, priorizarlos y presentarlos de forma que el usuario entienda rápido qué setup merece tiempo."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {painPoints.map((item, index) => (
          <article key={item} className="surface p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tide">Punto {index + 1}</p>
            <p className="mt-4 text-base leading-7 text-haze">{item}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
