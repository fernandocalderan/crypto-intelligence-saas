import { Section } from "../section";

const painPoints = [
  "La mayoría de alerts cripto llegan sin jerarquía, sin contexto y sin decir si realmente merece actuar.",
  "Una señal aislada no te dice si estás ante un setup operable, una watchlist o algo que debes descartar.",
  "Cuando el dato es débil o viene contaminado por heurísticas, esconderlo rompe confianza y empeora la decisión."
];

export default function ProblemSection() {
  return (
    <Section
      id="problema"
      eyebrow="Problema"
      title="El problema no es conseguir señales. Es filtrar cuáles merecen tiempo y riesgo."
      description="Crypto Intelligence parte de una idea simple: un operador no necesita más ruido. Necesita setups priorizados, con contexto operativo y con una explicación honesta de la calidad del dato."
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
