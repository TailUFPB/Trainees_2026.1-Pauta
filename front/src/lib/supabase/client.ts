import { createBrowserClient } from "@supabase/ssr";

// Cliente Supabase para o browser. Usa a anon key (segura no client); a sessão
// (e o access token usado pelo backend) fica gerenciada pelo próprio SDK.
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
