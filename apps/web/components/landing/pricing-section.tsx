import { PricingCard } from "../pricing-card";
import { Section } from "../section";
import { marketingPlans } from "../../lib/plans";

export default function PricingSection() {
  return (
    <Section
      id="pricing"
      eyebrow="Pricing"
      title="Pricing alineado con el producto real: teaser, setups completos y Telegram."
      description="Free sirve para probar el formato. Pro desbloquea el objeto comercial completo. Pro+ mantiene ese acceso y reserva la siguiente capa premium."
    >
      <div className="grid gap-5 lg:grid-cols-3">
        {marketingPlans.map((plan) => (
          <PricingCard key={plan.slug} plan={plan} isAuthenticated={false} />
        ))}
      </div>
    </Section>
  );
}
