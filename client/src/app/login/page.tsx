"use client";
import Link from "next/link";
import { useEffect } from "react";
import { useLoginModal } from "@/components/auth/LoginModalProvider";
import { Button } from "@/components/primitives/Button";
import { Container } from "@/components/primitives/Container";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { useSession } from "@/lib/hooks/useSession";

export default function LoginPage() {
  const { open } = useLoginModal();
  const { user } = useSession();

  useEffect(() => {
    if (!user) open("/");
  }, [user, open]);

  return (
    <Section spacing="default">
      <Container size="narrow" className="text-center">
        <Heading level={1} size="h1">
          {user ? "Você já está logado" : "Entrar no Pauta"}
        </Heading>
        <p className="mt-4 text-text-muted">
          {user
            ? `Sessão ativa como ${user.email}.`
            : "Abra o modal pra continuar com Google ou link mágico."}
        </p>
        <div className="mt-8 flex justify-center gap-3">
          {user ? (
            <Button asChild>
              <Link href="/">Voltar para a home</Link>
            </Button>
          ) : (
            <Button onClick={() => open("/")}>Abrir login</Button>
          )}
        </div>
      </Container>
    </Section>
  );
}
