import { redirect } from "next/navigation";

// O feed deixou de ser uma sub-página da conta e virou destino primário em
// /feed. Mantemos este redirect para não quebrar links antigos.
export default function ContaFeedRedirect() {
  redirect("/feed");
}
