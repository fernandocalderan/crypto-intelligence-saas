import { Section } from "../section";

const benefits = [
  "Reduce tiempo perdido en dashboards demasiado amplios.",
  "Alinea producto, UI y pricing alrededor de una propuesta comprensible.",
  "Permite lanzar una versión comercial sin esperar una suite institucional completa.",
  "Facilita el upgrade porque el valor del plan superior se ve en el propio feed."
];

export default function BenefitsSection() {
  return (
    <Section
      id="beneficios"
      eyebrow="Beneficios"
      title="Beneficios diseñados para el usuario y para la conversión."
      description="La landing no intenta vender magia. Intenta dejar claro por qué el producto ahorra tiempo y ordena mejor la lectura del mercado."
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {benefits.map((benefit) => (
          <article key={benefit} className="surface p-8">
            <p className="text-base leading-7 text-haze">{benefit}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
