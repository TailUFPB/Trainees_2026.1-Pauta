import Link from "next/link";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Heading } from "@/components/primitives/Heading";

// Estado vazio mostrado quando o usuário ainda não reportou nenhum problema.
// O CTA leva direto pra tela de reporte pra encurtar o caminho até a primeira ação.
export function EmptyState() {
  return (
    <Card className="mx-auto mt-12 max-w-xl text-center">
      <Heading level={2} size="h3">
        Você ainda não reportou nada.
      </Heading>
      <p className="mt-3 text-text-muted">
        Quando você reportar um problema, ele aparece aqui pra você acompanhar
        o status até a resolução.
      </p>
      <div className="mt-6">
        <Button asChild>
          <Link href="/reportar">Reportar primeiro problema</Link>
        </Button>
      </div>
    </Card>
  );
}
