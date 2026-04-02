import { PricingCard } from "../../components/pricing-card";
import { getSessionUser } from "../../lib/server-session";
import { marketingPlans } from "../../lib/plans";

type PricingPageProps = {
  searchParams?: {
    checkout?: string;
    plan?: string;
  };
};

export default async function PricingPage({ searchParams }: PricingPageProps) {
  const user = await getSessionUser();
  const selectedPlan = searchParams?.plan ?? null;
  const checkoutStatus = searchParams?.checkout ?? null;

  return (
    <div className="space-y-10 py-10">
      <section className="space-y-4">
        <span className="eyebrow">Pricing</span>
        <h1 className="section-title max-w-3xl">Planes simples para validar conversión y monetizar el feed del MVP.</h1>
        <p className="max-w-2xl text-base leading-7 text-haze">
          Free sirve para evaluar el formato. Pro y Pro+ desbloquean el acceso completo y ayudan a medir intención real
          de pago con Stripe.
        </p>
      </section>

      {checkoutStatus === "canceled" ? (
        <section className="rounded-3xl border border-red-300/20 bg-red-300/10 px-5 py-4 text-sm text-red-100">
          El checkout se canceló antes de completar el pago. Puedes volver a intentarlo cuando quieras.
        </section>
      ) : null}

      {checkoutStatus === "error" ? (
        <section className="rounded-3xl border border-red-300/20 bg-red-300/10 px-5 py-4 text-sm text-red-100">
          No se pudo iniciar el checkout. Revisa la configuración de Stripe o usa el modo mock para desarrollo.
        </section>
      ) : null}

      <section className="grid gap-5 lg:grid-cols-3">
        {marketingPlans.map((plan) => (
          <PricingCard
            key={plan.slug}
            plan={plan}
            isAuthenticated={Boolean(user)}
            currentPlan={user?.plan ?? null}
            highlight={selectedPlan === plan.slug}
          />
        ))}
      </section>
    </div>
  );
}
