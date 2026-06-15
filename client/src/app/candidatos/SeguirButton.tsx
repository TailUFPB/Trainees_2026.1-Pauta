"use client";

import { Check, Plus } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/primitives/Button";
import { api } from "@/lib/api/client";
import { useLoginModal } from "@/components/auth/LoginModalProvider";
import { useSession } from "@/lib/hooks/useSession";

// Botão "Seguir vereador". Expõe o endpoint POST /politicos/{id}/seguir, que
// antes não tinha entrada na UI. Sem query de status no backend, o estado
// "Seguindo" é otimista (vira true após o clique bem-sucedido).
export function SeguirButton({ politicoId }: { politicoId: string }) {
  const { user } = useSession();
  const { open } = useLoginModal();
  const [seguindo, setSeguindo] = useState(false);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(false);

  const handleClick = async () => {
    if (!user) {
      open("/candidatos");
      return;
    }
    setLoading(true);
    setErro(false);
    try {
      await api.seguirPolitico(politicoId);
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
      size="sm"
      loading={loading}
      disabled={seguindo}
      onClick={handleClick}
      aria-label={seguindo ? "Seguindo este vereador" : "Seguir este vereador"}
    >
      {seguindo ? (
        <>
          <Check className="h-4 w-4" aria-hidden /> Seguindo
        </>
      ) : (
        <>
          <Plus className="h-4 w-4" aria-hidden /> {erro ? "Tentar de novo" : "Seguir"}
        </>
      )}
    </Button>
  );
}
