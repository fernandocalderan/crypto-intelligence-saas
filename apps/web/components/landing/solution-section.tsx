import { Section } from "../section";

const payloadItems = [
  {
    title: "Estado operativo",
    description: "Cada setup se clasifica como EXECUTABLE, WATCHLIST, WAIT_CONFIRMATION o DISCARD para priorizar mejor."
  },
  {
    title: "Score y confianza",
    description: "La lectura se entrega con score visible y nivel de confianza legible para ordenar atención rápidamente."
  },
  {
    title: "Confirmaciones",
    description: "No ves solo una etiqueta. Ves qué piezas de confluencia sostienen la tesis y cuáles faltan."
  },
  {
    title: "Plan indicativo",
    description: "Cuando el setup lo permite, se muestran trigger, invalidación y objetivos indicativos sin falsa precisión."
  },
  {
    title: "Warnings de calidad",
    description: "Si el dato está contaminado por mock, inferencia o limitaciones del MVP, se expone de forma explícita."
  },
  {
    title: "Lectura accionable",
    description: "Resumen corto, tesis operativa y estructura para decidir qué mirar, qué esperar y cuándo no actuar."
  }
];

export default function SolutionSection() {
  return (
    <Section
      id="que-recibes"
      eyebrow="Qué recibes"
      title="Cada Setup PRO viene empaquetado como una lectura operativa completa."
      description="El producto no te entrega una alerta desnuda. Te entrega el activo, la dirección, el estado, el porqué y el plan base para interpretar el setup con más criterio."
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {payloadItems.map((item) => (
          <article key={item.title} className="surface p-8">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tide">{item.title}</p>
            <p className="mt-4 text-base leading-7 text-haze">{item.description}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
