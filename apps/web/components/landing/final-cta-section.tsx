import { CTAButton } from "../cta-button";

export default function FinalCtaSection() {
  return (
    <section className="surface flex flex-col gap-8 p-8 sm:p-10 lg:flex-row lg:items-center lg:justify-between">
      <div className="space-y-3">
        <span className="eyebrow">CTA final</span>
        <h2 className="section-title max-w-2xl">
          Si el formato te encaja, el siguiente paso es simple: desbloquear setups completos y Telegram.
        </h2>
        <p className="max-w-2xl text-base leading-7 text-haze">
          Crypto Intelligence está diseñado para reducir ruido y ordenar mejor la lectura del mercado. No sustituye tu
          criterio, pero sí te ahorra parte del trabajo previo.
        </p>
      </div>
      <div className="flex flex-wrap gap-4">
        <CTAButton
          href="/signup"
          label="Acceder a alertas Telegram"
          eventName="landing_final_primary_cta_clicked"
          eventContext="final_cta"
        />
        <CTAButton
          href="/pricing"
          label="Desbloquear setups completos"
          variant="secondary"
          eventName="landing_final_secondary_cta_clicked"
          eventContext="final_cta"
        />
      </div>
    </section>
  );
}
