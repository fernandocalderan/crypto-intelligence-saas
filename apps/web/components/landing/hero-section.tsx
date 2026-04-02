import { CTAButton } from "../cta-button";

const heroStats = [
  { label: "Señales MVP", value: "5" },
  { label: "Fuentes", value: "Binance + Bybit" },
  { label: "Modelo", value: "Free / Pro / Pro+" },
  { label: "Entrega", value: "Feed + score + tesis" }
];

export default function HeroSection() {
  return (
    <section className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
      <div className="space-y-6">
        <span className="eyebrow">Crypto Intelligence</span>
        <h1 className="max-w-4xl text-5xl font-semibold tracking-tight text-ink sm:text-6xl lg:text-7xl">
          Señales crypto para pasar del ruido a un criterio operativo repetible.
        </h1>
        <p className="max-w-2xl text-lg leading-8 text-haze sm:text-xl">
          Un SaaS para convertir datos de mercado en señales accionables con contexto, scoring y explicación clara,
          sin vender promesas ni disfrazar ruido como ventaja.
        </p>
        <div className="flex flex-wrap gap-4">
          <CTAButton
            href="/signup"
            label="Crear cuenta"
            eventName="landing_primary_cta_clicked"
            eventContext="hero"
          />
          <CTAButton
            href="/pricing"
            label="Ver pricing"
            variant="secondary"
            eventName="landing_secondary_cta_clicked"
            eventContext="hero"
          />
        </div>
      </div>

      <div className="surface grid-lines relative overflow-hidden p-8 sm:p-10">
        <div className="absolute right-0 top-0 h-44 w-44 rounded-full bg-moss/10 blur-3xl" />
        <div className="space-y-5">
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-haze">Hero snapshot</p>
          <div className="grid gap-4 sm:grid-cols-2">
            {heroStats.map((stat) => (
              <div key={stat.label} className="rounded-3xl border border-white/8 bg-black/10 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-haze">{stat.label}</p>
                <p className="mt-2 text-2xl font-semibold text-ink">{stat.value}</p>
              </div>
            ))}
          </div>
          <p className="muted">
            El producto está pensado para vender claridad operativa: qué pasa, por qué importa y qué nivel de
            convicción tiene la señal.
          </p>
        </div>
      </div>
    </section>
  );
}
