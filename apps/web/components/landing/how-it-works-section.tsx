import { Section } from "../section";

const steps = [
  {
    step: "01",
    title: "Ingesta de mercado",
    description: "El backend agrega snapshots normalizados desde exchanges y los deja listos para consumo."
  },
  {
    step: "02",
    title: "Detección de señales",
    description: "El motor evalúa volumen, breakout, funding, OI y liquidaciones con scoring consistente."
  },
  {
    step: "03",
    title: "Entrega comercial",
    description: "La UI convierte esa salida técnica en una alerta entendible, filtrada y monetizable."
  }
];

export default function HowItWorksSection() {
  return (
    <Section
      id="como-funciona"
      eyebrow="Cómo funciona"
      title="Tres capas para convertir datos de mercado en un producto vendible."
      description="El usuario no ve pipelines ni conectores. Ve un flujo claro: datos, señal y explicación."
    >
      <div className="grid gap-4 lg:grid-cols-3">
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
