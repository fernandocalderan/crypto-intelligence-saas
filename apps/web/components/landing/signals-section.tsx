import { Section } from "../section";

const fitItems = [
  "Trader discrecional que quiere setups mejor filtrados.",
  "Operativa táctica o swing corto con necesidad de priorizar rápido.",
  "Quien quiere ahorrar tiempo de análisis sin renunciar al criterio propio.",
  "Usuario que valora contexto operativo, no solo un ping de mercado."
];

const notFitItems = [
  "Scalping de segundos o ejecución ultra-rápida.",
  "Trading automático o bots que abren y cierran posiciones.",
  "Copy trading o delegar por completo la decisión.",
  "Promesas de dinero fácil o precisión falsa de micro-timing."
];

export default function SignalsSection() {
  return (
    <Section
      id="para-quien"
      eyebrow="Para quién es / no es"
      title="Pensado para operadores tácticos. No para automatizar el mercado."
      description="El producto ayuda a priorizar setups y a leer contexto. La ejecución y la gestión del riesgo siguen siendo del trader."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <article className="surface p-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-moss">Sí es para</p>
          <ul className="mt-5 space-y-4 text-base leading-7 text-haze">
            {fitItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="surface p-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-red-200">No es para</p>
          <ul className="mt-5 space-y-4 text-base leading-7 text-haze">
            {notFitItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
    </Section>
  );
}
