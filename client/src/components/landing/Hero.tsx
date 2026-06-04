import Link from "next/link";
import { ArrowRight, MapPin } from "lucide-react";
import { AuthGate } from "@/components/auth/AuthGate";
import { Button } from "@/components/primitives/Button";
import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { FadeUp } from "@/components/motion/FadeUp";
import { StylizedMap } from "./StylizedMap";

export function Hero() {
  return (
    <section className="pauta-grain relative overflow-hidden pt-12 pb-20 md:pt-20 md:pb-32">
      <Container>
        <div className="grid items-center gap-12 md:grid-cols-[1.1fr_1fr] md:gap-16">
          <div className="flex flex-col gap-8">
            <FadeUp>
              <Eyebrow>Plataforma cívica para a Paraíba</Eyebrow>
            </FadeUp>
            <FadeUp delay={0.05}>
              <h1 className="font-display font-bold leading-[1.02] tracking-[-0.03em] text-text text-[length:clamp(2.75rem,1.75rem+5vw,5.5rem)]">
                Veja o que a sua rua precisa.
                <br />
                <span className="text-accent">Cobre quem decide.</span>
              </h1>
            </FadeUp>
            <FadeUp delay={0.1}>
              <p className="max-w-lg text-lg text-text-muted">
                Mapeie problemas de infraestrutura em João Pessoa, Bayeux, Santa
                Rita e Campina Grande. Descubra quais vereadores defendem suas
                pautas.
              </p>
            </FadeUp>
            <FadeUp delay={0.15}>
              <div className="flex flex-wrap items-center gap-3">
                <AuthGate redirectTo="/reportar">
                  <Button size="lg" variant="primary" asChild>
                    <Link href="/reportar">
                      Reportar um problema <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </AuthGate>
                <Button size="lg" variant="secondary" asChild>
                  <Link href="/mapa">
                    <MapPin className="h-4 w-4" /> Ver o mapa da Paraíba
                  </Link>
                </Button>
              </div>
            </FadeUp>
          </div>
          <FadeUp delay={0.2} className="flex justify-center md:justify-end">
            <StylizedMap />
          </FadeUp>
        </div>
      </Container>
    </section>
  );
}
