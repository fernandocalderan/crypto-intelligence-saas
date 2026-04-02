import { Section } from "../section";

const solutionPillars = [
  {
    title: "Scoring visible",
    description: "Cada setup se publica con score, dirección, tesis y evidencia observable."
  },
  {
    title: "Acceso por plan",
    description: "El usuario Free prueba el formato y el usuario Pro desbloquea el feed completo."
  },
  {
    title: "Arquitectura modular",
    description: "Frontend, API y motor de señales pueden evolucionar sin acoplarse de forma rígida."
  }
];

export default function SolutionSection() {
  return (
    <Section
      id="solucion"
      eyebrow="Solución"
      title="Un feed accionable con contexto, scoring y una propuesta comercial simple."
      description="Crypto Intelligence empaqueta señales de mercado en un formato que el usuario puede entender en segundos y evaluar con criterio propio."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {solutionPillars.map((pillar) => (
          <article key={pillar.title} className="surface p-8">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tide">{pillar.title}</p>
            <p className="mt-4 text-base leading-7 text-haze">{pillar.description}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
