import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { AuthGate } from "@/components/auth/AuthGate";
import { Button } from "@/components/primitives/Button";
import { Container } from "@/components/primitives/Container";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { FadeUp } from "@/components/motion/FadeUp";

export function FinalCTA() {
  return (
    <Section tone="inverted" spacing="loose" className="pauta-grain overflow-hidden">
      <Container className="relative">
        <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
          <FadeUp>
            <Heading
              level={2}
              size="display"
              className="text-bg"
            >
              Sua cidade não precisa esperar a próxima eleição.
            </Heading>
          </FadeUp>
          <FadeUp delay={0.08} className="mt-8">
            <AuthGate redirectTo="/reportar">
              <Button size="lg" variant="invert" asChild>
                <Link href="/reportar">
                  Comece a reportar agora <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </AuthGate>
          </FadeUp>
          <FadeUp delay={0.14} className="mt-5">
            <p className="text-sm text-bg/70">
              Grátis. Anônimo se você preferir.
            </p>
          </FadeUp>
        </div>
      </Container>
    </Section>
  );
}
