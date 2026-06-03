import { getServerUser } from "@/lib/auth/getServerSession";
import { HeaderClient } from "./HeaderClient";

export async function SiteHeader() {
  const user = await getServerUser();
  return <HeaderClient initialUserEmail={user?.email ?? null} />;
}
