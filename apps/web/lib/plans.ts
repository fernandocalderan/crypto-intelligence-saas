export type MarketingPlan = {
  slug: "free" | "pro" | "pro_plus";
  name: string;
  price: string;
  cadence: string;
  eyebrow: string;
  description: string;
  bullets: string[];
  cta: string;
  featured?: boolean;
};

export const marketingPlans: MarketingPlan[] = [
  {
    slug: "free",
    name: "Free",
    price: "0€",
    cadence: "/mes",
    eyebrow: "Teaser",
    description: "Prueba el formato.",
    bullets: [
      "Teaser de setups",
      "Dashboard limitado",
      "Prueba antes del upgrade"
    ],
    cta: "Probar el feed"
  },
  {
    slug: "pro",
    name: "Pro",
    price: "39€",
    cadence: "/mes",
    eyebrow: "Core",
    description: "El producto completo.",
    bullets: [
      "Setups completos",
      "Telegram inmediato",
      "Histórico visible"
    ],
    cta: "Desbloquear setups completos",
    featured: true
  },
  {
    slug: "pro_plus",
    name: "Pro+",
    price: "99€",
    cadence: "/mes",
    eyebrow: "Premium",
    description: "Capa premium futura.",
    bullets: [
      "Todo lo de Pro",
      "Breakdown ampliado",
      "Espacio para seguimiento"
    ],
    cta: "Acceder a alertas Telegram"
  }
];
