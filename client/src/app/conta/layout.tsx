import { redirect } from "next/navigation";
import { getServerUser } from "@/lib/auth/getServerSession";
import { AccountNav } from "./AccountNav";

export default async function ContaLayout({ children }: { children: React.ReactNode }) {
  const user = await getServerUser();
  if (!user) {
    redirect("/?login=1&redirectTo=/conta");
  }
  return (
    <div className="flex flex-col">
      <AccountNav />
      {children}
    </div>
  );
}
