import Image from "next/image";

import { CTAButton } from "../cta-button";

const heroVariants = [
  {
    label: "Variante A",
    headline: "Setups PRO crypto con contexto. No señales sueltas.",
    subheadline:
      "Confluencia, estado operativo, confirmaciones y plan indicativo para operadores que quieren criterio táctico, no ruido."
  },
  {
    label: "Variante B",
    headline: "Menos ruido. Más setups operables.",
    subheadline:
      "Plataforma de Setups PRO para trading táctico y swing corto, con alertas inmediatas por Telegram y dashboard con contexto completo."
  },
  {
    label: "Variante C",
    headline: "Detecta setups operables. No persigas señales vacías.",
    subheadline:
      "Crypto Intelligence prioriza setups con estado operativo, confirmaciones y warnings explícitos para decidir más rápido sin vender automatización."
  }
] as const;

const activeHero = heroVariants[1];

const trustStrip = [
  "Setups PRO con confluencia",
  "Estado operativo + plan indicativo",
  "Warnings de calidad del dato",
  "Alertas inmediatas por Telegram",
  "Dashboard con setups activos e histórico"
];

const productGuards = [
  "No es trading automático",
  "No es copy trading",
  "No está pensado para scalping agresivo",
  "No sustituye tu criterio operativo"
];

export default function HeroSection() {
  return (
    <section className="space-y-6">
      <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
        <div className="space-y-6">
          <div className="space-y-3">
            <span className="eyebrow">Setups PRO</span>
            <p className="max-w-2xl text-sm font-medium uppercase tracking-[0.16em] text-haze">
              Plataforma de setups crypto accionables para trading táctico y swing corto
            </p>
          </div>

          <h1 className="max-w-5xl text-5xl font-semibold tracking-tight text-ink sm:text-6xl lg:text-7xl">
            {activeHero.headline}
          </h1>

          <p className="max-w-3xl text-lg leading-8 text-haze sm:text-xl">{activeHero.subheadline}</p>

          <p className="max-w-3xl text-base leading-7 text-haze">
            Crypto Intelligence detecta setups, los clasifica por estado operativo, los distribuye por Telegram y los
            mantiene visibles en dashboard. No ejecuta operaciones ni promete resultados automáticos.
          </p>

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
                <p className="mt-2 text-lg font-medium text-ink">Trading táctico con setups priorizados, no con alerts vacías.</p>
              </div>
            </div>

            <div className="rounded-3xl border border-moss/20 bg-moss/10 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-moss">Lo que sí recibes</p>
              <ul className="mt-4 space-y-3 text-sm leading-7 text-ink">
                <li>Setup por activo con dirección, score y confianza.</li>
                <li>Confirmaciones y estado operativo claros.</li>
                <li>Trigger, invalidación y TP indicativos cuando aplica.</li>
                <li>Warnings explícitos si el dato no está fully validated.</li>
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
