import type { Metadata } from "next";
import dynamic from "next/dynamic";

import HeroSection from "../components/landing/hero-section";
import SectionLoading from "../components/landing/section-loading";

const ProblemSection = dynamic(() => import("../components/landing/problem-section"), {
  loading: () => <SectionLoading />
});
const SolutionSection = dynamic(() => import("../components/landing/solution-section"), {
  loading: () => <SectionLoading />
});
const HowItWorksSection = dynamic(() => import("../components/landing/how-it-works-section"), {
  loading: () => <SectionLoading />
});
const SignalsSection = dynamic(() => import("../components/landing/signals-section"), {
  loading: () => <SectionLoading />
});
const AlertExampleSection = dynamic(() => import("../components/landing/alert-example-section"), {
  loading: () => <SectionLoading />
});
const BenefitsSection = dynamic(() => import("../components/landing/benefits-section"), {
  loading: () => <SectionLoading />
});
const HistorySection = dynamic(() => import("../components/landing/history-section"), {
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
  title: "Setups PRO crypto con alertas Telegram",
  description:
    "Plataforma de Setups PRO accionables para trading táctico: confluencia, estado operativo, confirmaciones, plan indicativo, Telegram y dashboard con histórico.",
  openGraph: {
    title: "Setups PRO crypto con alertas Telegram",
    description:
      "Menos ruido. Más setups operables. Contexto operativo, confirmaciones, plan indicativo y dashboard con setups activos e histórico visible."
  }
};

export default function HomePage() {
  return (
    <div className="space-y-14 pb-16 pt-8 sm:space-y-20 sm:pt-12">
      <HeroSection />
      <ProblemSection />
      <SolutionSection />
      <HowItWorksSection />
      <SignalsSection />
      <AlertExampleSection />
      <BenefitsSection />
      <HistorySection />
      <PricingSection />
      <ObjectionsSection />
      <FinalCtaSection />
    </div>
  );
}
