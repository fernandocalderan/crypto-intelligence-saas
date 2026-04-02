import { Section } from "../section";

const faqs = [
  {
    question: "¿Es para scalping?",
    answer: "No es un producto pensado para scalping rápido. Está orientado a trading táctico y swing corto con setups priorizados."
  },
  {
    question: "¿Ejecuta operaciones?",
    answer: "No. Detecta setups, los clasifica y los distribuye. La ejecución sigue siendo del trader."
  },
  {
    question: "¿Qué horizonte tienen los setups?",
    answer: "Están pensados para lectura táctica y swing corto, no para automatización de micro-timing."
  },
  {
    question: "¿Qué recibo en Telegram?",
    answer: "El setup estructurado: activo, dirección, estado operativo, resumen, confirmaciones, plan indicativo y warnings de calidad."
  },
  {
    question: "¿Qué veo en dashboard?",
    answer: "Setups PRO, señales base, bloque de histórico y configuración de alertas. El producto mantiene coherencia entre web y Telegram."
  },
  {
    question: "¿Qué pasa si el dato no es fiable?",
    answer: "Se expone con warnings explícitos. El producto no intenta ocultar contaminación mock, inferencias o limitaciones del MVP."
  },
  {
    question: "¿Cuál es la diferencia entre señal y setup?",
    answer: "La señal es una lectura base del engine. El setup es la capa superior con confluencia, estado operativo y plan de acción indicativo."
  }
];

export default function ObjectionsSection() {
  return (
    <Section
      id="faq"
      eyebrow="FAQ"
      title="Preguntas que importan antes de pagar por una herramienta operativa."
      description="Respuestas breves, sin hype y sin vender capacidades que el producto no tiene."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        {faqs.map((item) => (
          <article key={item.question} className="surface p-8">
            <h3 className="text-xl font-semibold text-ink">{item.question}</h3>
            <p className="mt-4 text-base leading-7 text-haze">{item.answer}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
