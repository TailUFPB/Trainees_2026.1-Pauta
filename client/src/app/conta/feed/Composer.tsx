"use client";
import { VenetianMask } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/primitives/Button";
import type { ItemFeed } from "@/lib/api/feed";
import { criarPublicacao } from "@/lib/api/publicacoes";

const LIMITE = 1000;

interface Props {
  onPublicada: (item: ItemFeed) => void;
}

export function Composer({ onPublicada }: Props) {
  const [conteudo, setConteudo] = useState("");
  const [anonimo, setAnonimo] = useState(false);
  const [submetendo, setSubmetendo] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const conteudoTrim = conteudo.trim();
  const podeEnviar =
    conteudoTrim.length > 0 && conteudo.length <= LIMITE && !submetendo;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!podeEnviar) return;
    setSubmetendo(true);
    setErro(null);
    try {
      const nova = await criarPublicacao({
        conteudo: conteudoTrim,
        anonimo,
      });
      onPublicada({
        tipo: "publicacao",
        id: nova.id,
        conteudo: nova.conteudo,
        imagem_url: nova.imagem_url,
        anonimo: nova.anonimo,
        autor_nome: nova.autor_nome,
        created_at: nova.created_at,
      });
      setConteudo("");
      setAnonimo(false);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Erro ao publicar.");
    } finally {
      setSubmetendo(false);
    }
  };

  return (
    <form
      onSubmit={submit}
      className="mb-6 flex flex-col gap-3 rounded-lg border border-border bg-surface p-4"
      aria-label="Nova publicação"
    >
      <label htmlFor="composer-conteudo" className="sr-only">
        Conteúdo da publicação
      </label>
      <textarea
        id="composer-conteudo"
        value={conteudo}
        onChange={(e) => setConteudo(e.target.value)}
        placeholder="O que tá rolando na sua rua?"
        rows={3}
        maxLength={LIMITE}
        aria-describedby="composer-helper"
        className="min-h-[80px] resize-y rounded-md border border-border bg-bg px-3 py-2 text-text outline-none placeholder:text-text-muted focus:border-accent"
      />
      <div className="flex items-center justify-between gap-3">
        <label
          htmlFor="composer-anonimo"
          className="inline-flex cursor-pointer items-center gap-2 text-sm"
        >
          <input
            id="composer-anonimo"
            type="checkbox"
            className="h-4 w-4 accent-accent"
            checked={anonimo}
            onChange={(e) => setAnonimo(e.target.checked)}
          />
          <span className="inline-flex items-center gap-1">
            <VenetianMask aria-hidden className="h-4 w-4" />
            Publicar como anônimo
          </span>
        </label>
        <div
          id="composer-helper"
          aria-live="polite"
          className="text-xs text-text-muted tabular-nums"
        >
          {conteudo.length} / {LIMITE}
        </div>
      </div>
      {erro && (
        <div
          role="alert"
          className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
        >
          {erro}
        </div>
      )}
      <div className="flex justify-end">
        <Button
          type="submit"
          variant="primary"
          loading={submetendo}
          disabled={!podeEnviar}
        >
          {submetendo ? "Publicando…" : "Publicar"}
        </Button>
      </div>
    </form>
  );
}
