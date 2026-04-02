const plans = [
  {
    name: "Starter",
    price: "€49",
    copy: "Validación inicial para traders y pequeños desks.",
    bullets: ["3 señales activas", "Dashboard diario", "Alertas por email"]
  },
  {
    name: "Pro",
    price: "€149",
    copy: "Producto central para monetizar el MVP con valor claro.",
    bullets: ["5 señales activas", "Refresh intradía", "Tesis y scoring explicables"]
  },
  {
    name: "Desk",
    price: "Custom",
    copy: "Onboarding asistido para equipos con necesidades específicas.",
    bullets: ["Workspaces privados", "Feeds custom", "Integración API futura"]
  }
];

export default function PricingPage() {
  return (
    <div className="space-y-10 py-10">
      <section className="space-y-4">
        <span className="eyebrow">Pricing</span>
        <h1 className="section-title max-w-3xl">Precios simples para un MVP que debe vender claridad, no complejidad.</h1>
        <p className="max-w-2xl text-base leading-7 text-haze">
          La monetización inicial se apoya en señales bien explicadas, onboarding rápido y una diferencia clara entre usuarios casuales y desks.
        </p>
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        {plans.map((plan) => (
          <article
            key={plan.name}
            className={`surface flex flex-col gap-6 p-8 ${plan.name === "Pro" ? "border-moss/40 bg-gradient-to-b from-moss/10 to-slate/80" : ""}`}
          >
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tide">{plan.name}</p>
              <h2 className="text-4xl font-semibold text-ink">{plan.price}</h2>
              <p className="text-base leading-7 text-haze">{plan.copy}</p>
            </div>
            <ul className="space-y-3 text-sm text-haze">
              {plan.bullets.map((bullet) => (
                <li key={bullet} className="rounded-2xl border border-white/8 bg-black/10 px-4 py-3">
                  {bullet}
                </li>
              ))}
            </ul>
            <button className="mt-auto rounded-full border border-white/15 px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-ink transition hover:border-moss hover:text-moss">
              Seleccionar
            </button>
          </article>
        ))}
      </section>
    </div>
  );
}

