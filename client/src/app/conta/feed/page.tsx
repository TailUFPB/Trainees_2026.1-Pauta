import { Container } from "@/components/primitives/Container";
import { buscarFeed } from "@/lib/api/feed.server";
import { FeedView } from "./FeedView";

// Server component: busca a primeira página do feed com SSR para evitar
// flash de skeleton em condições de rede boa. A paginação é client-side.
export default async function FeedPage() {
  const inicial = await buscarFeed({ limite: 20 });
  return (
    <Container className="max-w-2xl py-6">
      <h1 className="mb-6 text-2xl font-semibold tracking-tight text-text">
        Feed
      </h1>
      <FeedView inicial={inicial} />
    </Container>
  );
}
