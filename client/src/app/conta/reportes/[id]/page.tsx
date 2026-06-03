import { notFound, redirect } from "next/navigation";
import { Container } from "@/components/primitives/Container";
import { Section } from "@/components/primitives/Section";
import { apiServer } from "@/lib/api/serverClient";
import { getServerUser } from "@/lib/auth/getServerSession";
import type { Problema } from "@/lib/api/types";
import { ReporteDetail } from "./ReporteDetail";

// Página server-side: exige sessão e busca o problema pelo backend via endpoint
// dedicado do autor (`GET /usuarios/me/problemas/:id`). O backend retorna 404
// diretamente se o usuário não for o autor ou o reporte não existir.
export default async function DetalheReportePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const user = await getServerUser();
  if (!user) redirect(`/?login=1&redirectTo=/conta/reportes/${id}`);

  let problema: Problema;
  try {
    problema = await apiServer.problemaPorIdComoAutor(id);
  } catch {
    // 404 do backend quando não é o autor (ou reporte inexistente) — tratamos como
    // not-found pro front, sem distinção (não vazar existência do reporte).
    notFound();
  }

  return (
    <Section spacing="tight">
      <Container size="wide">
        <ReporteDetail p={problema} />
      </Container>
    </Section>
  );
}
