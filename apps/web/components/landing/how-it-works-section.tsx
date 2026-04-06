import { Section } from "../section";

const steps = [
  {
    step: "01",
    title: "Detecta setups",
    description: "Normaliza mercado y agrupa confluencias."
  },
  {
    step: "02",
    title: "Clasifica el setup",
    description: "Estado, score y calidad del dato."
  },
  {
    step: "03",
    title: "Telegram + dashboard",
    description: "Alerta rápida y lectura completa."
  }
];

export default function HowItWorksSection() {
  return (
    <Section
      id="como-funciona"
      eyebrow="Cómo funciona"
      title="Tres pasos."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {steps.map((step) => (
          <article key={step.step} className="surface p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-moss">{step.step}</p>
            <h3 className="mt-3 text-xl font-semibold text-ink">{step.title}</h3>
            <p className="mt-3 text-sm leading-6 text-haze">{step.description}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
