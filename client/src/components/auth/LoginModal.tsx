"use client";
import { Mail } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/primitives/Button";
import { Input } from "@/components/primitives/Input";
import { Modal } from "@/components/primitives/Modal";
import { createClient } from "@/lib/supabase/client";

type Status =
  | { kind: "idle" }
  | { kind: "loading-oauth" }
  | { kind: "loading-magic" }
  | { kind: "success-magic"; email: string }
  | { kind: "error"; message: string };

interface Props {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}

export function LoginModal({ open, onOpenChange }: Props) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  const supabase = createClient();

  const handleGoogle = async () => {
    setStatus({ kind: "loading-oauth" });
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) setStatus({ kind: "error", message: error.message });
  };

  const handleMagic = async (e: FormEvent) => {
    e.preventDefault();
    setStatus({ kind: "loading-magic" });
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) setStatus({ kind: "error", message: error.message });
    else setStatus({ kind: "success-magic", email });
  };

  const reset = () => setStatus({ kind: "idle" });

  return (
    <Modal
      open={open}
      onOpenChange={(v) => {
        if (!v) reset();
        onOpenChange(v);
      }}
      title="Entre pra reportar e acompanhar"
      description="Acesso por Google ou link mágico no e-mail."
    >
      {status.kind === "success-magic" ? (
        <div className="flex flex-col items-start gap-4">
          <div className="grid h-12 w-12 place-items-center rounded-pill bg-success/10 text-success">
            <Mail className="h-5 w-5" />
          </div>
          <div>
            <p className="font-medium text-text">Confira seu e-mail</p>
            <p className="mt-1 text-sm text-text-muted">
              Mandamos um link mágico para <strong>{status.email}</strong>. Abra no
              celular ou desktop pra entrar.
            </p>
          </div>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Fechar
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-5">
          {status.kind === "error" ? (
            <div
              role="alert"
              className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
            >
              {status.message}
            </div>
          ) : null}
          <Button
            variant="secondary"
            size="lg"
            onClick={handleGoogle}
            loading={status.kind === "loading-oauth"}
            className="w-full"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden>
              <path fill="#4285F4" d="M21.6 12.23c0-.78-.07-1.53-.2-2.25H12v4.26h5.4a4.62 4.62 0 0 1-2 3.03v2.52h3.24c1.9-1.75 2.99-4.33 2.99-7.56z"/>
              <path fill="#34A853" d="M12 22c2.7 0 4.96-.9 6.62-2.43l-3.24-2.52c-.9.6-2.04.96-3.38.96-2.6 0-4.8-1.76-5.58-4.12H3.07v2.6A10 10 0 0 0 12 22z"/>
              <path fill="#FBBC05" d="M6.42 13.89A6 6 0 0 1 6.1 12c0-.66.12-1.3.32-1.89V7.5H3.07A10 10 0 0 0 2 12c0 1.62.39 3.15 1.07 4.5l3.35-2.61z"/>
              <path fill="#EA4335" d="M12 6.04c1.47 0 2.78.5 3.81 1.5l2.86-2.86A10 10 0 0 0 12 2 10 10 0 0 0 3.07 7.5l3.35 2.61C7.2 7.8 9.4 6.04 12 6.04z"/>
            </svg>
            Continuar com Google
          </Button>
          <div className="flex items-center gap-3 text-xs text-text-muted">
            <span className="h-px flex-1 bg-border" />
            ou
            <span className="h-px flex-1 bg-border" />
          </div>
          <form onSubmit={handleMagic} className="flex flex-col gap-3">
            <label className="flex flex-col gap-2 text-sm text-text">
              <span className="font-medium">E-mail</span>
              <Input
                type="email"
                required
                placeholder="voce@exemplo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={status.kind === "loading-magic"}
              className="w-full"
            >
              Enviar link mágico
            </Button>
          </form>
          <p className="text-center text-xs text-text-muted">
            Ao continuar, você concorda com os Termos e a Política de Privacidade.
          </p>
        </div>
      )}
    </Modal>
  );
}
