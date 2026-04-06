import { CTAButton } from "../cta-button";

export default function FinalCtaSection() {
  return (
    <section className="surface flex flex-col gap-6 p-8 sm:p-10 lg:flex-row lg:items-center lg:justify-between">
      <div className="space-y-2">
        <span className="eyebrow">CTA final</span>
        <h2 className="section-title max-w-2xl">Desbloquea Setups PRO y Telegram.</h2>
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
