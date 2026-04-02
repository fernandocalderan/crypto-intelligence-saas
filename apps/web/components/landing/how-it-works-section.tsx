import { Section } from "../section";

const steps = [
  {
    step: "01",
    title: "Mercado normalizado + detección",
    description: "El backend agrega snapshots desde exchanges y detecta setups de confluencia sobre ese contexto."
  },
  {
    step: "02",
    title: "Clasificación operativa",
    description: "Cada setup se clasifica por estado operativo, score, confianza y calidad del dato."
  },
  {
    step: "03",
    title: "Alertas inmediatas por Telegram",
    description: "Los usuarios PRO reciben el setup estructurado por Telegram cuando merece distribución inmediata."
  },
  {
    step: "04",
    title: "Dashboard con contexto + histórico",
    description: "El mismo setup queda visible en dashboard con confirmaciones, plan indicativo y bloque de histórico."
  }
];

export default function HowItWorksSection() {
  return (
    <Section
      id="como-funciona"
      eyebrow="Cómo funciona"
      title="Cuatro pasos para pasar del mercado al setup legible."
      description="La experiencia está pensada para entender rápido qué ocurre, por qué importa y qué conviene hacer con esa lectura."
    >
      <div className="grid gap-4 lg:grid-cols-4">
        {steps.map((step) => (
          <article key={step.step} className="surface p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-moss">{step.step}</p>
            <h3 className="mt-4 text-2xl font-semibold text-ink">{step.title}</h3>
            <p className="mt-4 text-base leading-7 text-haze">{step.description}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
