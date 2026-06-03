import { notFound, redirect } from "next/navigation";
import { Container } from "@/components/primitives/Container";
import { Section } from "@/components/primitives/Section";
import { apiServer } from "@/lib/api/serverClient";
import { getServerUser } from "@/lib/auth/getServerSession";
import type { Problema } from "@/lib/api/types";
import { ReporteDetail } from "./ReporteDetail";

// Página server-side: exige sessão e busca o problema pelo backend já como
// autor (rota `/problemas/:id`). Se o usuário logado não for o autor, o
// backend devolve `ProblemaPublico` (sem `autor_id` nem `descricao`) — nesse
// caso devolvemos 404, porque a tela "Minha conta > Detalhe" só faz sentido
// pro próprio autor.
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
    const resp = await apiServer.problemaPorIdComoAutor(id);
    if (!("autor_id" in resp)) notFound();
    problema = resp as Problema;
  } catch {
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
