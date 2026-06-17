"use client";
import { ImagePlus, VenetianMask, X } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/primitives/Button";
import type { ItemFeed } from "@/lib/api/feed";
import { criarPublicacao } from "@/lib/api/publicacoes";

const LIMITE = 1000;
const TIPOS_FOTO_OK = ["image/jpeg", "image/png", "image/webp"];
const MAX_FOTO_BYTES = 8 * 1024 * 1024; // 8 MB — mesmo limite do backend.

interface Props {
  onPublicada: (item: ItemFeed) => void;
}

export function Composer({ onPublicada }: Props) {
  const [conteudo, setConteudo] = useState("");
  const [anonimo, setAnonimo] = useState(false);
  const [foto, setFoto] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [submetendo, setSubmetendo] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const inputFotoRef = useRef<HTMLInputElement>(null);

  // Libera o object URL do preview quando troca ou desmonta (evita vazamento).
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const conteudoTrim = conteudo.trim();
  const podeEnviar =
    conteudoTrim.length > 0 && conteudo.length <= LIMITE && !submetendo;

  const limparFoto = () => {
    setFoto(null);
    setPreviewUrl((url) => {
      if (url) URL.revokeObjectURL(url);
      return null;
    });
    if (inputFotoRef.current) inputFotoRef.current.value = "";
  };

  const onSelecionarFoto = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!TIPOS_FOTO_OK.includes(file.type)) {
      setErro("Formato não suportado. Use JPEG, PNG ou WEBP.");
      e.target.value = "";
      return;
    }
    if (file.size > MAX_FOTO_BYTES) {
      setErro("Imagem maior que 8 MB.");
      e.target.value = "";
      return;
    }
    setErro(null);
    setPreviewUrl((url) => {
      if (url) URL.revokeObjectURL(url);
      return URL.createObjectURL(file);
    });
    setFoto(file);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!podeEnviar) return;
    setSubmetendo(true);
    setErro(null);
    try {
      const nova = await criarPublicacao({
        conteudo: conteudoTrim,
        anonimo,
        foto,
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
      limparFoto();
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

      {previewUrl && (
        <div className="relative w-fit">
          {/* Preview local (object URL). CSP permite blob:. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt="Pré-visualização da foto selecionada"
            className="max-h-56 rounded-md border border-border object-cover"
          />
          <button
            type="button"
            onClick={limparFoto}
            aria-label="Remover foto"
            className="absolute right-2 top-2 inline-flex h-7 w-7 items-center justify-center rounded-full bg-bg/80 text-text shadow-1 backdrop-blur hover:bg-bg"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>
      )}

      <input
        ref={inputFotoRef}
        type="file"
        accept={TIPOS_FOTO_OK.join(",")}
        onChange={onSelecionarFoto}
        className="sr-only"
        aria-hidden
        tabIndex={-1}
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => inputFotoRef.current?.click()}
            className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text"
          >
            <ImagePlus className="h-4 w-4" aria-hidden />
            {foto ? "Trocar foto" : "Adicionar foto"}
          </button>
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
        </div>
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
