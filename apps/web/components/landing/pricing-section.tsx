import { PricingCard } from "../pricing-card";
import { Section } from "../section";
import { marketingPlans } from "../../lib/plans";

export default function PricingSection() {
  return (
    <Section
      id="pricing"
      eyebrow="Pricing"
      title="Tres planes. Un producto claro."
      description="Free prueba. Pro desbloquea. Pro+ amplía."
    >
      <div className="grid gap-5 lg:grid-cols-3">
        {marketingPlans.map((plan) => (
          <PricingCard key={plan.slug} plan={plan} isAuthenticated={false} />
        ))}
      </div>
    </Section>
  );
}
