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
    description: "Para probar el feed, entender el formato de Setups PRO y ver cómo se presenta el contexto antes del upgrade.",
    bullets: [
      "Vista teaser de setups y señales base",
      "Acceso limitado al dashboard y al histórico visible",
      "Ideal para validar si el formato encaja con tu operativa"
    ],
    cta: "Probar el feed"
  },
  {
    slug: "pro",
    name: "Pro",
    price: "39€",
    cadence: "/mes",
    eyebrow: "Core",
    description: "Acceso completo a Setups PRO con estado operativo, confirmaciones, plan indicativo y alertas inmediatas por Telegram.",
    bullets: [
      "Setups completos con score, confianza y estado operativo",
      "Confirmaciones, trigger, invalidación y objetivos indicativos",
      "Alertas Telegram y acceso al histórico visible de setups"
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
    description: "La misma capa completa de Setups PRO, con espacio reservado para seguimiento premium y futuras capas de performance avanzada.",
    bullets: [
      "Todo lo incluido en Pro",
      "Breakdown ampliado y prioridad sobre futuras capas premium",
      "Preparado para seguimiento operativo más profundo"
    ],
    cta: "Acceder a alertas Telegram"
  }
];
