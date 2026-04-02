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
const PricingSection = dynamic(() => import("../components/landing/pricing-section"), {
  loading: () => <SectionLoading />
});
const ObjectionsSection = dynamic(() => import("../components/landing/objections-section"), {
  loading: () => <SectionLoading />
});
const FinalCtaSection = dynamic(() => import("../components/landing/final-cta-section"), {
  loading: () => <SectionLoading />
});

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
      <PricingSection />
      <ObjectionsSection />
      <FinalCtaSection />
    </div>
  );
}
