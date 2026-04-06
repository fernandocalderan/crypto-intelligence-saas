import type { Metadata } from "next";
import dynamic from "next/dynamic";

import HeroSection from "../components/landing/hero-section";
import SectionLoading from "../components/landing/section-loading";

const SolutionSection = dynamic(() => import("../components/landing/solution-section"), {
  loading: () => <SectionLoading />
});
const HowItWorksSection = dynamic(() => import("../components/landing/how-it-works-section"), {
  loading: () => <SectionLoading />
});
const SignalsSection = dynamic(() => import("../components/landing/signals-section"), {
  loading: () => <SectionLoading />
});
const PricingSection = dynamic(() => import("../components/landing/pricing-section"), {
  loading: () => <SectionLoading />
});
const ObjectionsSection = dynamic(() => import("../components/landing/objections-section"), {
  loading: () => <SectionLoading />
});
const FinalCtaSection = dynamic(() => import("../components/landing/final-cta-section"), {
  loading: () => <SectionLoading />
});

export const metadata: Metadata = {
  title: "Setups PRO crypto para Telegram y dashboard",
  description:
    "Setups PRO para trading táctico: contexto, estado operativo, Telegram y dashboard.",
  openGraph: {
    title: "Setups PRO crypto para Telegram y dashboard",
    description:
      "Menos ruido. Más setups operables. Telegram, dashboard y contexto útil."
  }
};

export default function HomePage() {
  return (
    <div className="space-y-12 pb-16 pt-8 sm:space-y-16 sm:pt-12">
      <HeroSection />
      <SolutionSection />
      <HowItWorksSection />
      <SignalsSection />
      <PricingSection />
      <ObjectionsSection />
      <FinalCtaSection />
    </div>
  );
}
