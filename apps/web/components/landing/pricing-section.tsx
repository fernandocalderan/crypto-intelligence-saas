import { PricingCard } from "../pricing-card";
import { Section } from "../section";
import { marketingPlans } from "../../lib/plans";

export default function PricingSection() {
  return (
    <Section
      id="pricing"
      eyebrow="Pricing"
      title="Tres planes para reducir fricción y convertir sin exagerar el mensaje."
      description="Free sirve para validar el formato. Pro y Pro+ sirven para monetizar el acceso completo de forma clara."
    >
      <div className="grid gap-5 lg:grid-cols-3">
        {marketingPlans.map((plan) => (
          <PricingCard key={plan.slug} plan={plan} isAuthenticated={false} />
        ))}
      </div>
    </Section>
  );
}
