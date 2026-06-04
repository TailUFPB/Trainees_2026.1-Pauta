import { createServerSupabase } from "@/lib/supabase/server";

export async function getServerUser() {
  const supabase = await createServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  return user;
}

/**
 * Retorna a sessão Supabase inteira (com access_token) para usos server-side
 * que precisam autenticar fetches ao backend FastAPI.
 *
 * NÃO usar em código exposto ao client — o access_token é segredo.
 */
export async function getServerSession() {
  const supabase = await createServerSupabase();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session;
}
