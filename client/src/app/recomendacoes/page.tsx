import { redirect } from "next/navigation";

// As recomendações passaram a ser uma aba do hub de Candidatos. Mantemos este
// redirect para não quebrar links antigos (footer, e-mails, notificações).
export default function RecomendacoesRedirect() {
  redirect("/candidatos/recomendacoes");
}
