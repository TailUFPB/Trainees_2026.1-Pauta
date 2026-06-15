import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/auth/getServerSession";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST() {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ detail: "Sessao ausente." }, { status: 401 });
  }

  const response = await fetch(`${API_URL}/notificacoes/teste`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
    cache: "no-store",
  });

  const body = await response.text();
  return new NextResponse(body, {
    status: response.status,
    headers: { "Content-Type": response.headers.get("Content-Type") ?? "application/json" },
  });
}
