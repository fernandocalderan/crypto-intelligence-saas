import { Section } from "../section";

const fitItems = [
  "Trader discrecional.",
  "Swing corto o táctica.",
  "Menos tiempo de análisis.",
  "Más contexto antes de decidir."
];

const notFitItems = [
  "Scalping rápido.",
  "Trading automático.",
  "Copy trading.",
  "Promesas irreales."
];

export default function SignalsSection() {
  return (
    <Section
      id="para-quien"
      eyebrow="Para quién es / no es"
      title="Para operadores tácticos."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <article className="surface p-6">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-moss">Sí es para</p>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-haze">
            {fitItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="surface p-6">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-red-200">No es para</p>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-haze">
            {notFitItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
    </Section>
  );
}
