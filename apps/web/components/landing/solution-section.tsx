import { Section } from "../section";

const payloadItems = [
  {
    title: "Estado operativo",
    description: "EXECUTABLE, WATCHLIST o espera."
  },
  {
    title: "Score y confianza",
    description: "Prioridad visible al instante."
  },
  {
    title: "Confirmaciones",
    description: "Qué confirma el setup."
  },
  {
    title: "Plan indicativo",
    description: "Trigger, invalidación y TP."
  }
];

export default function SolutionSection() {
  return (
    <Section
      id="que-recibes"
      eyebrow="Qué recibes"
      title="Cada Setup PRO resume lo esencial."
      description="Activo, dirección, estado y plan."
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {payloadItems.map((item) => (
          <article key={item.title} className="surface p-6">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tide">{item.title}</p>
            <p className="mt-3 text-sm leading-6 text-haze">{item.description}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
