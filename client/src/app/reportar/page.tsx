"use client";
import { Camera, Loader2, MapPin } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Badge } from "@/components/primitives/Badge";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Input } from "@/components/primitives/Input";
import { Section } from "@/components/primitives/Section";
import { api } from "@/lib/api/client";
import type { Problema } from "@/lib/api/types";
import { useSession } from "@/lib/hooks/useSession";
import { useLoginModal } from "@/components/auth/LoginModalProvider";

export default function ReportarPage() {
  const { user, loading: sessionLoading } = useSession();
  const { open } = useLoginModal();
  const [foto, setFoto] = useState<File | null>(null);
  const [coord, setCoord] = useState<{ lat: number; lng: number } | null>(null);
  const [descricao, setDescricao] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<Problema | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGeo = () => {
    if (!("geolocation" in navigator)) {
      setError("Geolocalização não disponível neste dispositivo.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => setCoord({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setError("Não foi possível obter sua localização."),
    );
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!user) {
      open("/reportar");
      return;
    }
    if (!foto || !coord) {
      setError("Foto e localização são obrigatórias.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const problema = await api.criarProblema({
        foto,
        lat: coord.lat,
        lng: coord.lng,
        descricao: descricao || undefined,
      });
      setResult(problema);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao enviar.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Section spacing="default">
      <Container size="narrow">
        <Eyebrow>Reportar problema</Eyebrow>
        <Heading level={1} size="h1" className="mt-4">
          Conta o que tá quebrado.
        </Heading>
        <p className="mt-4 text-text-muted">
          Tire uma foto e marca sua localização. A IA classifica automaticamente.
        </p>

        {sessionLoading ? (
          <div className="mt-8 flex items-center gap-2 text-text-muted">
            <Loader2 className="h-4 w-4 animate-spin" /> Verificando sessão…
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
            <label className="flex flex-col gap-2 text-sm font-medium text-text">
              Foto do problema
              <div className="flex items-center gap-3">
                <label className="inline-flex h-11 cursor-pointer items-center gap-2 rounded-md border border-border-strong bg-surface px-4 text-sm text-text hover:border-text">
                  <Camera className="h-4 w-4" />
                  {foto ? foto.name : "Escolher arquivo"}
                  <input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    className="hidden"
                    onChange={(e) => setFoto(e.target.files?.[0] ?? null)}
                  />
                </label>
              </div>
            </label>

            <div className="flex flex-col gap-2 text-sm font-medium text-text">
              Localização
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleGeo}
                  size="md"
                >
                  <MapPin className="h-4 w-4" />
                  {coord ? "Atualizar" : "Usar minha localização"}
                </Button>
                {coord ? (
                  <Badge tone="success">
                    {coord.lat.toFixed(4)}, {coord.lng.toFixed(4)}
                  </Badge>
                ) : null}
              </div>
            </div>

            <label className="flex flex-col gap-2 text-sm font-medium text-text">
              Descrição (opcional)
              <Input
                type="text"
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                placeholder="Ex: buraco fundo na esquina da padaria"
              />
            </label>

            {error ? (
              <div
                role="alert"
                className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
              >
                {error}
              </div>
            ) : null}

            <Button
              type="submit"
              size="lg"
              loading={submitting}
              disabled={!foto || !coord}
            >
              {user ? "Enviar reporte" : "Entrar e reportar"}
            </Button>
          </form>
        )}

        {result ? (
          <Card className="mt-10">
            <Eyebrow tone="muted">Resultado</Eyebrow>
            <Heading level={2} size="h3" className="mt-2 capitalize">
              {(result.tipo_problema ?? "outro").replace(/_/g, " ")}
            </Heading>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge tone="accent">Severidade: {result.severidade ?? "—"}</Badge>
              <Badge>
                Confiança: {result.confianca != null ? `${(result.confianca * 100).toFixed(0)}%` : "—"}
              </Badge>
              <Badge>Status: {result.status}</Badge>
            </div>
            {result.resumo_llm ? (
              <p className="mt-4 text-sm text-text-muted">{result.resumo_llm}</p>
            ) : null}
          </Card>
        ) : null}
      </Container>
    </Section>
  );
}
