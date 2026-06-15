import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { buscarFeed } from "@/lib/api/feed.server";
import { getServerUser } from "@/lib/auth/getServerSession";
import { FeedGate } from "./FeedGate";
import { FeedView } from "./FeedView";

// Feed comunitário — destino primário público (linkado no navbar). Como o
// backend exige sessão, deslogados veem um gate de login; logados recebem a
// primeira página via SSR para evitar flash de skeleton.
export default async function FeedPage() {
  const user = await getServerUser();

  return (
    <Container className="max-w-2xl py-6">
      <Eyebrow>Comunidade</Eyebrow>
      <Heading level={1} size="h1" className="mb-6 mt-2">
        Feed
      </Heading>
      {user ? (
        <FeedView inicial={await buscarFeed({ limite: 20 })} />
      ) : (
        <FeedGate />
      )}
    </Container>
  );
}
