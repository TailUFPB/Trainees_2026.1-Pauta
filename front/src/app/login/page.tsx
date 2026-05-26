"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const supabase = createClient();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUserEmail(data.user?.email ?? null));
  }, [supabase]);

  async function entrar(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const { error } = await supabase.auth.signInWithPassword({ email, password: senha });
    setMsg(error ? error.message : "Login efetuado.");
    if (!error) setUserEmail(email);
  }

  async function cadastrar() {
    setMsg(null);
    const { error } = await supabase.auth.signUp({ email, password: senha });
    setMsg(error ? error.message : "Cadastro criado — confira seu email se a confirmação estiver ativa.");
  }

  async function sair() {
    await supabase.auth.signOut();
    setUserEmail(null);
    setMsg("Sessão encerrada.");
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="text-2xl font-semibold tracking-tight">Entrar</h1>

      {userEmail && (
        <p className="mt-3 rounded border border-emerald-200 bg-emerald-50 p-3 text-sm">
          Logado como <strong>{userEmail}</strong>.{" "}
          <button onClick={sair} className="underline">Sair</button>
        </p>
      )}

      <form onSubmit={entrar} className="mt-5 flex flex-col gap-3">
        <input
          type="email"
          required
          placeholder="email@exemplo.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded border border-zinc-300 px-3 py-2"
        />
        <input
          type="password"
          required
          placeholder="senha"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          className="rounded border border-zinc-300 px-3 py-2"
        />
        <div className="flex gap-2">
          <button type="submit" className="rounded bg-zinc-900 px-4 py-2 text-white">
            Entrar
          </button>
          <button type="button" onClick={cadastrar} className="rounded border border-zinc-300 px-4 py-2">
            Criar conta
          </button>
        </div>
      </form>

      {msg && <p className="mt-4 text-sm text-zinc-600">{msg}</p>}
      <p className="mt-6 text-xs text-zinc-500">
        Requer <code>NEXT_PUBLIC_SUPABASE_URL</code> e <code>NEXT_PUBLIC_SUPABASE_ANON_KEY</code> no <code>.env.local</code>.
      </p>
    </div>
  );
}
