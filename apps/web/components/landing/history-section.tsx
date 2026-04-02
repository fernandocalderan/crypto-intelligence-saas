import { Section } from "../section";

const historyBlocks = [
  {
    title: "Setups activos",
    description: "Los setups relevantes siguen visibles dentro del dashboard mientras están vivos operativamente."
  },
  {
    title: "Setups recientes",
    description: "El producto no se limita a detectar. También deja lectura reciente para revisar qué apareció y cómo evolucionó."
  },
  {
    title: "Seguimiento honesto",
    description: "Sin prometer analytics institucionales aún. Solo visibilidad útil de setups activos, cerrados o invalidados."
  }
];

export default function HistorySection() {
  return (
    <Section
      id="historico"
      eyebrow="Histórico visible"
      title="No solo detecta setups. También los mantiene visibles para lectura y seguimiento."
      description="El dashboard incluye setups activos y un bloque histórico reciente para no perder el hilo del contexto operativo una vez que el setup aparece."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {historyBlocks.map((item) => (
          <article key={item.title} className="surface p-8">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tide">{item.title}</p>
            <p className="mt-4 text-base leading-7 text-haze">{item.description}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
