import { Section } from "../section";

const historyBlocks = [
  {
    title: "Setups activos",
    description: "Siguen visibles."
  },
  {
    title: "Setups recientes",
    description: "No desaparecen."
  },
  {
    title: "Seguimiento honesto",
    description: "Sin promesas falsas."
  }
];

export default function HistorySection() {
  return (
    <Section
      id="historico"
      eyebrow="Histórico visible"
      title="También deja histórico."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {historyBlocks.map((item) => (
          <article key={item.title} className="surface p-6">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tide">{item.title}</p>
            <p className="mt-3 text-sm leading-6 text-haze">{item.description}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
