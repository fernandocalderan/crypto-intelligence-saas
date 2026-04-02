import { Section } from "../section";

const signals = [
  {
    name: "Volume Spike",
    description: "Detecta expansión de flujo frente a la media reciente."
  },
  {
    name: "Range Breakout",
    description: "Señala rupturas con contexto de rango y confirmación."
  },
  {
    name: "Funding Extreme",
    description: "Identifica desequilibrios de positioning en perps."
  },
  {
    name: "OI Divergence",
    description: "Mide divergencias entre precio y open interest."
  },
  {
    name: "Liquidation Cluster",
    description: "Resume eventos de limpieza de posicionamiento."
  }
];

export default function SignalsSection() {
  return (
    <Section
      id="senales"
      eyebrow="Señales"
      title="Cinco señales del MVP empaquetadas para vender criterio, no humo."
      description="Cada señal tiene un rol claro dentro del producto y una explicación visible para que el usuario entienda qué está viendo."
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {signals.map((signal) => (
          <article key={signal.name} className="surface p-6">
            <h3 className="text-lg font-semibold text-ink">{signal.name}</h3>
            <p className="mt-3 text-sm leading-7 text-haze">{signal.description}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
