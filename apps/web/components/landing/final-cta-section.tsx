import { CTAButton } from "../cta-button";

export default function FinalCtaSection() {
  return (
    <section className="surface flex flex-col gap-8 p-8 sm:p-10 lg:flex-row lg:items-center lg:justify-between">
      <div className="space-y-3">
        <span className="eyebrow">CTA final</span>
        <h2 className="section-title max-w-2xl">
          Crea la cuenta, revisa el feed y decide después si el formato justifica el upgrade.
        </h2>
        <p className="max-w-2xl text-base leading-7 text-haze">
          El objetivo del MVP no es impresionar con complejidad. Es demostrar que el producto ahorra tiempo y comunica
          valor de forma comercialmente clara.
        </p>
      </div>
      <div className="flex flex-wrap gap-4">
        <CTAButton
          href="/signup"
          label="Ir a signup"
          eventName="landing_final_primary_cta_clicked"
          eventContext="final_cta"
        />
        <CTAButton
          href="/pricing"
          label="Comparar planes"
          variant="secondary"
          eventName="landing_final_secondary_cta_clicked"
          eventContext="final_cta"
        />
      </div>
    </section>
  );
}
