import type { Metadata } from "next";

import { PricingCard } from "../../components/pricing-card";
import { getSessionUser } from "../../lib/server-session";
import { marketingPlans } from "../../lib/plans";

type PricingPageProps = {
  searchParams?: {
    checkout?: string;
    plan?: string;
  };
};

export const metadata: Metadata = {
  title: "Pricing de Setups PRO",
  description:
    "Compara Free, Pro y Pro+ para acceder a Setups PRO crypto, alertas Telegram y dashboard con contexto operativo e histórico visible.",
  openGraph: {
    title: "Pricing de Setups PRO",
    description:
      "Free para probar el formato. Pro para desbloquear setups completos y alertas Telegram. Pro+ para la capa premium futura."
  }
};

export default async function PricingPage({ searchParams }: PricingPageProps) {
  const user = await getSessionUser();
  const selectedPlan = searchParams?.plan ?? null;
  const checkoutStatus = searchParams?.checkout ?? null;

  return (
    <div className="space-y-10 py-10">
      <section className="space-y-4">
        <span className="eyebrow">Pricing</span>
        <h1 className="section-title max-w-3xl">Planes alineados con el producto real: Setups PRO, Telegram y dashboard operativo.</h1>
        <p className="max-w-2xl text-base leading-7 text-haze">
          Free deja probar el formato. Pro desbloquea el setup completo con contexto operativo y Telegram. Pro+ mantiene
          ese acceso y reserva la siguiente capa premium de seguimiento.
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
