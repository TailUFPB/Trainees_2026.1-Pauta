import { Suspense } from "react";
import { redirect } from "next/navigation";
import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { ImpactStats } from "@/components/landing/ImpactStats";
import { CandidatesTeaser } from "@/components/landing/CandidatesTeaser";
import { FinalCTA } from "@/components/landing/FinalCTA";
import { getServerUser } from "@/lib/auth/getServerSession";

// Visitante vê a vitrine das funcionalidades. Logado não precisa de marketing —
// vai direto pra Visão geral da conta.
export default async function Home() {
  const user = await getServerUser();
  if (user) redirect("/conta");

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
