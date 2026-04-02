import { Section } from "../section";

const noPoints = [
  "Señales aisladas sin decir si hay setup real.",
  "Alerts sin contexto operativo ni plan base.",
  "Promesas de precisión que el dato no puede sostener.",
  "Ocultar cuando el dato es incompleto o viene degradado."
];

const yesPoints = [
  "Setups estructurados por confluencia.",
  "Estado operativo explícito para priorizar mejor.",
  "Confirmaciones visibles y warnings honestos.",
  "Plan indicativo para decidir más rápido sin vender automatización."
];

export default function BenefitsSection() {
  return (
    <Section
      id="por-que-diferente"
      eyebrow="Por qué es diferente"
      title="No intenta parecer un oráculo. Intenta ser una herramienta de lectura operativa."
      description="La diferencia no está en gritar más fuerte. Está en mostrar qué setup existe, qué lo confirma y qué limitaciones tiene el dato antes de pedirte atención."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <article className="surface p-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-red-200">No</p>
          <ul className="mt-5 space-y-4 text-base leading-7 text-haze">
            {noPoints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="surface p-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-moss">Sí</p>
          <ul className="mt-5 space-y-4 text-base leading-7 text-haze">
            {yesPoints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
    </Section>
  );
}
