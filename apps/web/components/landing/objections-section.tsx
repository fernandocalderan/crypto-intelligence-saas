import { Section } from "../section";

const objections = [
  {
    question: "¿Esto promete rentabilidad?",
    answer: "No. El producto organiza señales y contexto. La decisión final sigue siendo del usuario."
  },
  {
    question: "¿Necesito experiencia avanzada?",
    answer: "No necesariamente. El formato intenta reducir fricción explicando por qué la señal existe y qué evidencia la respalda."
  },
  {
    question: "¿Puedo probar antes de pagar?",
    answer: "Sí. El plan Free deja ver una parte del feed para validar si el formato te encaja."
  }
];

export default function ObjectionsSection() {
  return (
    <Section
      id="objeciones"
      eyebrow="Objeciones"
      title="Las dudas razonables se resuelven mejor con claridad que con promesas."
      description="Esta parte de la landing está pensada para reducir fricción antes del registro y hacer más comprensible el upgrade."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {objections.map((item) => (
          <article key={item.question} className="surface p-8">
            <h3 className="text-xl font-semibold text-ink">{item.question}</h3>
            <p className="mt-4 text-base leading-7 text-haze">{item.answer}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
