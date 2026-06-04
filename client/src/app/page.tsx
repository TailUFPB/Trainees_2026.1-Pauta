import { Suspense } from "react";
import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { ImpactStats } from "@/components/landing/ImpactStats";
import { CandidatesTeaser } from "@/components/landing/CandidatesTeaser";
import { FinalCTA } from "@/components/landing/FinalCTA";

export default function Home() {
  return (
    <>
      <Hero />
      <HowItWorks />
      <Suspense fallback={<div />}>
        <ImpactStats />
      </Suspense>
      <Suspense fallback={<div />}>
        <CandidatesTeaser />
      </Suspense>
      <FinalCTA />
    </>
  );
}
