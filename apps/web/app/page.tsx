import Link from "next/link";

const pillars = [
  {
    title: "Signals with context",
    description: "No solo alertas. Cada señal incluye tesis, score y condiciones de invalidez."
  },
  {
    title: "Modular data stack",
    description: "Diseñado para enchufar exchanges, on-chain y order flow sin reescribir la UI."
  },
  {
    title: "VPS ready",
    description: "La base ya incluye Docker, Postgres y reverse proxy para pasar a producción."
  }
];

const stats = [
  { label: "MVP signals", value: "5" },
  { label: "Target latency", value: "< 60s" },
  { label: "Initial markets", value: "Spot + Perps" }
];

export default function HomePage() {
  return (
    <div className="space-y-14 pb-16 pt-8 sm:space-y-20 sm:pt-12">
      <section className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
        <div className="space-y-6">
          <span className="eyebrow">Crypto Intelligence SaaS</span>
          <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-ink sm:text-6xl lg:text-7xl">
            Señales accionables para convertir ruido de mercado en decisiones.
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-haze sm:text-xl">
            Base preparada para vender inteligencia crypto con dashboard, backend modular y scoring listo para evolucionar desde mocks hacia datos reales.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/dashboard"
              className="rounded-full bg-moss px-6 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d]"
            >
              Ver dashboard
            </Link>
            <Link
              href="/pricing"
              className="rounded-full border border-white/15 px-6 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-ink transition hover:border-tide hover:text-tide"
            >
              Revisar pricing
            </Link>
          </div>
        </div>
        <div className="surface grid-lines relative overflow-hidden p-8 sm:p-10">
          <div className="absolute right-0 top-0 h-44 w-44 rounded-full bg-moss/10 blur-3xl" />
          <div className="space-y-6">
            <p className="text-sm font-medium uppercase tracking-[0.24em] text-haze">Snapshot</p>
            <div className="space-y-4">
              {stats.map((stat) => (
                <div key={stat.label} className="flex items-center justify-between border-b border-white/8 pb-4">
                  <span className="text-sm uppercase tracking-[0.16em] text-haze">{stat.label}</span>
                  <span className="text-2xl font-semibold text-ink">{stat.value}</span>
                </div>
              ))}
            </div>
            <p className="muted">
              El MVP ya está estructurado para que el frontend y el motor de señales evolucionen sin acoplarse de forma rígida.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        {pillars.map((pillar) => (
          <article key={pillar.title} className="surface p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tide">Built for iteration</p>
            <h2 className="mt-4 text-2xl font-semibold text-ink">{pillar.title}</h2>
            <p className="mt-3 text-base leading-7 text-haze">{pillar.description}</p>
          </article>
        ))}
      </section>

      <section className="surface flex flex-col gap-8 p-8 sm:p-10 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-3">
          <span className="eyebrow">Go To Market</span>
          <h2 className="section-title max-w-2xl">Define 5 señales, fija el scoring y ya tendrás algo vendible.</h2>
          <p className="max-w-2xl text-base leading-7 text-haze">
            El mayor riesgo no es técnico. Es lanzar un dashboard elegante sin una propuesta clara de señal y explicación para el cliente.
          </p>
        </div>
        <Link
          href="/login"
          className="inline-flex items-center justify-center rounded-full border border-moss/40 bg-moss/10 px-6 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-moss transition hover:border-moss hover:bg-moss hover:text-canvas"
        >
          Simular acceso
        </Link>
      </section>
    </div>
  );
}

