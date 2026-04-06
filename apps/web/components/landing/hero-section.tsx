import Image from "next/image";

import { CTAButton } from "../cta-button";

const heroVariants = [
  {
    label: "Variante A",
    headline: "Setups PRO con contexto.",
    subheadline: "Telegram y dashboard para trading táctico."
  },
  {
    label: "Variante B",
    headline: "Menos ruido. Más setups operables.",
    subheadline: "Setups para 12h–72h, con Telegram y dashboard."
  },
  {
    label: "Variante C",
    headline: "Detecta setups. No señales sueltas.",
    subheadline: "Estado operativo, plan indicativo y warnings."
  }
] as const;

const activeHero = heroVariants[1];

const trustStrip = [
  "Confluencia",
  "Estado operativo",
  "Plan indicativo",
  "Telegram",
  "Histórico"
];

const productGuards = [
  "No auto-trading",
  "No copy trading",
  "No scalping",
  "No sustituye criterio"
];

export default function HeroSection() {
  return (
    <section className="space-y-6">
      <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
        <div className="space-y-6">
          <div className="space-y-2">
            <span className="eyebrow">Setups PRO</span>
            <p className="text-sm font-medium uppercase tracking-[0.16em] text-haze">Trading táctico. No señales sueltas.</p>
          </div>

          <h1 className="max-w-5xl text-5xl font-semibold tracking-tight text-ink sm:text-6xl lg:text-7xl">
            {activeHero.headline}
          </h1>

          <p className="max-w-3xl text-lg leading-8 text-haze sm:text-xl">{activeHero.subheadline}</p>

          <div className="flex flex-wrap gap-4">
            <CTAButton
              href="/pricing"
              label="Ver Setups PRO"
              eventName="landing_primary_cta_clicked"
              eventContext="hero"
            />
            <CTAButton
              href="/dashboard"
              label="Probar el feed"
              variant="secondary"
              eventName="landing_secondary_cta_clicked"
              eventContext="hero"
            />
          </div>
        </div>

        <div className="surface grid-lines relative overflow-hidden p-8 sm:p-10">
          <div className="absolute right-0 top-0 h-48 w-48 rounded-full bg-moss/10 blur-3xl" />
          <div className="space-y-5">
            <div className="flex items-center gap-4">
              <div className="overflow-hidden rounded-3xl border border-white/10 bg-black/10 p-2">
                <Image src="/logomarca.png" alt="Crypto Intelligence" width={88} height={88} className="h-20 w-20 object-cover" />
              </div>
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-haze">Crypto Intelligence</p>
                <p className="mt-2 text-lg font-medium text-ink">Setups claros para decidir rápido.</p>
              </div>
            </div>

            <div className="rounded-3xl border border-moss/20 bg-moss/10 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-moss">Recibes</p>
              <ul className="mt-4 space-y-2 text-sm leading-6 text-ink">
                <li>Activo, dirección y score.</li>
                <li>Estado operativo.</li>
                <li>Niveles indicativos.</li>
                <li>Warnings si el dato flojea.</li>
              </ul>
            </div>

            <div className="rounded-3xl border border-white/8 bg-black/10 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-haze">Lo que no vende este producto</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {productGuards.map((guard) => (
                  <span
                    key={guard}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-haze"
                  >
                    {guard}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="surface grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-5">
        {trustStrip.map((item) => (
          <div key={item} className="rounded-2xl border border-white/8 bg-black/10 px-4 py-4 text-sm font-medium text-ink">
            {item}
          </div>
        ))}
      </div>
    </section>
  );
}
