import { Section } from "../section";

const faqs = [
  {
    question: "¿Es para scalping?",
    answer: "No. Está pensado para trading táctico y swing corto."
  },
  {
    question: "¿Ejecuta operaciones?",
    answer: "No. Detecta y prioriza; tú ejecutas."
  },
  {
    question: "¿Qué horizonte tienen los setups?",
    answer: "Normalmente 12h–72h."
  },
  {
    question: "¿Qué recibo en Telegram?",
    answer: "Activo, dirección, estado y plan base."
  },
  {
    question: "¿Cuál es la diferencia entre señal y setup?",
    answer: "La señal es base. El setup añade confluencia y plan."
  }
];

export default function ObjectionsSection() {
  return (
    <Section
      id="faq"
      eyebrow="FAQ"
      title="FAQ corta."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        {faqs.map((item) => (
          <article key={item.question} className="surface p-6">
            <h3 className="text-lg font-semibold text-ink">{item.question}</h3>
            <p className="mt-3 text-sm leading-6 text-haze">{item.answer}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
