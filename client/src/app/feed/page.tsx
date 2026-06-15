import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { buscarFeed } from "@/lib/api/feed.server";
import { getServerUser } from "@/lib/auth/getServerSession";
import { FeedView } from "./FeedView";

// Feed comunitário — leitura pública (GET /feed é público). Publicar exige
// login: o Composer só aparece logado; deslogado vê um CTA de entrar.
export default async function FeedPage() {
  const [user, inicial] = await Promise.all([
    getServerUser(),
    buscarFeed({ limite: 20 }),
  ]);

  return (
    <Container className="max-w-2xl py-6">
      <Eyebrow>Comunidade</Eyebrow>
      <Heading level={1} size="h1" className="mb-6 mt-2">
        Feed
      </Heading>
      <FeedView inicial={inicial} podePublicar={!!user} />
    </Container>
  );
}
