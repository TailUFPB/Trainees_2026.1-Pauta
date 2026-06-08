"use client";

import { useState } from "react";
import { PostCard } from "@/components/feed/PostCard";
import { buscarFeedClient, type ItemFeed } from "@/lib/api/feed";
import { Composer } from "./Composer";

interface Props {
  inicial: ItemFeed[];
}

const PAGINA = 20;

export function FeedView({ inicial }: Props) {
  const [itens, setItens] = useState<ItemFeed[]>(inicial);
  const [carregando, setCarregando] = useState(false);
  // Se a página inicial veio incompleta, já sabemos que não há mais nada.
  const [acabou, setAcabou] = useState(inicial.length < PAGINA);

  const handleNova = (nova: ItemFeed) =>
    setItens((prev) => [nova, ...prev]);

  const carregarMais = async () => {
    if (carregando || acabou || itens.length === 0) return;
    setCarregando(true);
    try {
      const cursor = itens[itens.length - 1].created_at;
      const mais = await buscarFeedClient({ cursor, limite: PAGINA });
      if (mais.length < PAGINA) setAcabou(true);
      if (mais.length > 0) setItens((prev) => [...prev, ...mais]);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <>
      <Composer onPublicada={handleNova} />

      {itens.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-8 text-center">
          <p className="text-text-muted">
            Nada por aqui ainda. Seja o primeiro a publicar.
          </p>
        </div>
      ) : (
        <ul className="flex flex-col gap-4">
          {itens.map((item) => (
            <li key={`${item.tipo}-${item.id}`}>
              <PostCard item={item} />
            </li>
          ))}
        </ul>
      )}

      {!acabou && itens.length > 0 && (
        <div className="mt-6 flex justify-center">
          <button
            type="button"
            onClick={carregarMais}
            disabled={carregando}
            className="inline-flex min-h-[44px] items-center justify-center rounded-md border border-border bg-surface px-5 text-sm font-medium text-text transition hover:border-accent/40 disabled:opacity-50"
          >
            {carregando ? "Carregando…" : "Carregar mais"}
          </button>
        </div>
      )}
    </>
  );
}
