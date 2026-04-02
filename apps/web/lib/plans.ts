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
    eyebrow: "Validación",
    description: "Para evaluar el enfoque, recibir una muestra de señales y entender el formato antes de pagar.",
    bullets: [
      "Hasta 2 señales visibles",
      "Snapshot de mercado y dashboard base",
      "Acceso a copy y tesis resumida"
    ],
    cta: "Crear cuenta"
  },
  {
    slug: "pro",
    name: "Pro",
    price: "39€",
    cadence: "/mes",
    eyebrow: "Core plan",
    description: "Acceso completo al feed del MVP con scoring, tesis y contexto suficiente para tomar decisiones propias.",
    bullets: [
      "Todas las señales activas del MVP",
      "Tesis, evidencia y score completos",
      "Acceso continuo al dashboard"
    ],
    cta: "Pasar a Pro",
    featured: true
  },
  {
    slug: "pro_plus",
    name: "Pro+",
    price: "99€",
    cadence: "/mes",
    eyebrow: "Power users",
    description: "Para operadores que quieren el mismo feed más prioridad en nuevas capas de producto y soporte beta.",
    bullets: [
      "Todo lo incluido en Pro",
      "Prioridad en nuevas señales beta",
      "Acceso temprano a mejoras del panel"
    ],
    cta: "Ir a Pro+"
  }
];
