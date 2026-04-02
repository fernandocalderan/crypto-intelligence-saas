"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import type { MarketingPlan } from "../lib/plans";
import { trackEvent } from "../lib/tracking";

type PricingCardProps = {
  plan: MarketingPlan;
  isAuthenticated?: boolean;
  currentPlan?: string | null;
  interactive?: boolean;
  highlight?: boolean;
};

export function PricingCard({
  plan,
  isAuthenticated = false,
  currentPlan,
  interactive = true,
  highlight = false
}: PricingCardProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const isCurrentPlan = currentPlan === plan.slug;
  const featured = highlight || plan.featured;

  async function handleClick() {
    trackEvent({
      event: "pricing_cta_clicked",
      context: "pricing",
      properties: {
        plan: plan.slug
      }
    });

    if (!interactive) {
      router.push("/pricing");
      return;
    }

    if (plan.slug === "free") {
      router.push("/signup");
      return;
    }

    if (!isAuthenticated) {
      router.push(`/signup?plan=${plan.slug}`);
      return;
    }

    if (isCurrentPlan) {
      router.push("/dashboard");
      return;
    }

    setLoading(true);
    const response = await fetch("/api/billing/checkout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ plan: plan.slug })
    });
    const payload = await response.json();
    setLoading(false);

    if (!response.ok) {
      router.push(`/pricing?checkout=error&plan=${plan.slug}`);
      return;
    }

    trackEvent({
      event: "checkout_started",
      context: "pricing",
      properties: {
        plan: plan.slug,
        mock: Boolean(payload.is_mock)
      }
    });
    window.location.assign(payload.checkout_url);
  }

  return (
    <article
      className={`surface flex h-full flex-col gap-6 p-8 ${
        featured ? "border-moss/40 bg-gradient-to-b from-moss/10 to-slate/80 shadow-glow" : ""
      }`}
    >
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-tide">{plan.eyebrow}</p>
          {isCurrentPlan ? (
            <span className="rounded-full border border-moss/30 bg-moss/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-moss">
              Plan actual
            </span>
          ) : null}
        </div>
        <div>
          <h2 className="text-3xl font-semibold text-ink">{plan.name}</h2>
          <p className="mt-2 text-4xl font-semibold text-ink">
            {plan.price}
            <span className="text-base font-medium text-haze">{plan.cadence}</span>
          </p>
        </div>
        <p className="text-base leading-7 text-haze">{plan.description}</p>
      </div>

      <ul className="space-y-3 text-sm text-haze">
        {plan.bullets.map((bullet) => (
          <li key={bullet} className="rounded-2xl border border-white/8 bg-black/10 px-4 py-3">
            {bullet}
          </li>
        ))}
      </ul>

      <button
        type="button"
        disabled={loading}
        onClick={handleClick}
        className={`mt-auto rounded-full px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] transition ${
          featured
            ? "bg-moss text-canvas hover:bg-[#d2ff9d]"
            : "border border-white/15 text-ink hover:border-moss hover:text-moss"
        } disabled:cursor-not-allowed disabled:opacity-70`}
      >
        {loading ? "Redirigiendo..." : isCurrentPlan ? "Ir al dashboard" : plan.cta}
      </button>
    </article>
  );
}
