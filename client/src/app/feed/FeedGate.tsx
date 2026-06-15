"use client";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Heading } from "@/components/primitives/Heading";
import { useLoginModal } from "@/components/auth/LoginModalProvider";

// Gate de login do feed: o feed comunitário é destino primário, mas publicar e
// ler exigem sessão (GET /feed é autenticado). Mostrado a usuários deslogados.
export function FeedGate() {
  const { open } = useLoginModal();
  return (
    <Card className="mx-auto mt-8 max-w-xl text-center">
      <Heading level={2} size="h3">
        Entre para ver o feed da comunidade.
      </Heading>
      <p className="mt-3 text-text-muted">
        Acompanhe o que vizinhos estão reportando e publique suas próprias
        atualizações — anônimo, se preferir.
      </p>
      <div className="mt-6">
        <Button onClick={() => open("/feed")}>Entrar</Button>
      </div>
    </Card>
  );
}
