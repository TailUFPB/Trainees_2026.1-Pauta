"use client";

import { Bell, Check } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/primitives/Button";
import { api } from "@/lib/api/client";
import { useLoginModal } from "@/components/auth/LoginModalProvider";
import { useSession } from "@/lib/hooks/useSession";

// Botão "Seguir problema". Expõe POST /problemas/{id}/inscrever, que não tinha
// entrada na UI. Quem segue recebe alertas de mudança de status. Estado otimista.
export function SeguirProblemaButton({ problemaId }: { problemaId: string }) {
  const { user } = useSession();
  const { open } = useLoginModal();
  const [seguindo, setSeguindo] = useState(false);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(false);

  const handleClick = async () => {
    if (!user) {
      open(`/problemas/${problemaId}`);
      return;
    }
    setLoading(true);
    setErro(false);
    try {
      await api.inscreverProblema(problemaId);
      setSeguindo(true);
    } catch {
      setErro(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      type="button"
      variant={seguindo ? "secondary" : "primary"}
      loading={loading}
      disabled={seguindo}
      onClick={handleClick}
      aria-label={seguindo ? "Seguindo este problema" : "Seguir este problema"}
    >
      {seguindo ? (
        <>
          <Check className="h-4 w-4" aria-hidden /> Seguindo
        </>
      ) : (
        <>
          <Bell className="h-4 w-4" aria-hidden />{" "}
          {erro ? "Tentar de novo" : "Seguir problema"}
        </>
      )}
    </Button>
  );
}
