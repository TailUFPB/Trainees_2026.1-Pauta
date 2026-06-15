import { getServerSession } from "@/lib/auth/getServerSession";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Apenas estes prefixos podem ser encaminhados — evita que o proxy vire um
// forwarder aberto. O primeiro segmento do path precisa estar nesta lista.
const ALLOWED_PREFIXES = new Set([
  "problemas",
  "recomendacoes",
  "politicos",
  "usuarios",
]);

// Cabeçalhos hop-by-hop não devem ser repassados entre conexões distintas.
const HOP_BY_HOP = new Set([
  "content-encoding",
  "content-length",
  "transfer-encoding",
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "upgrade",
]);

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: Request, ctx: RouteContext): Promise<Response> {
  const { path } = await ctx.params;

  if (!path?.length || !ALLOWED_PREFIXES.has(path[0])) {
    return new Response("Not Found", { status: 404 });
  }

  const search = new URL(request.url).search;
  const target = `${API_URL}/${path.join("/")}${search}`;

  // Anexa o token server-side; nunca exposto ao browser.
  const session = await getServerSession();
  const headers = new Headers();
  if (session) {
    headers.set("Authorization", `Bearer ${session.access_token}`);
  }

  const method = request.method;
  const hasBody = method === "POST" || method === "PUT" || method === "PATCH";

  const contentType = request.headers.get("content-type");
  if (hasBody && contentType) {
    headers.set("Content-Type", contentType);
  }

  const init: RequestInit & { duplex?: "half" } = {
    method,
    headers,
  };

  if (hasBody) {
    init.body = request.body;
    // Necessário ao encaminhar o stream cru da request (multipart/form-data).
    init.duplex = "half";
  }

  let upstream: Response;
  try {
    upstream = await fetch(target, init);
  } catch {
    // Backend inacessível: não vaza o erro/stack cru ao cliente.
    return new Response(JSON.stringify({ detail: "backend indisponível" }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      responseHeaders.set(key, value);
    }
  });

  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export function GET(request: Request, ctx: RouteContext): Promise<Response> {
  return proxy(request, ctx);
}

export function POST(request: Request, ctx: RouteContext): Promise<Response> {
  return proxy(request, ctx);
}

export function PUT(request: Request, ctx: RouteContext): Promise<Response> {
  return proxy(request, ctx);
}

export function PATCH(request: Request, ctx: RouteContext): Promise<Response> {
  return proxy(request, ctx);
}

export function DELETE(request: Request, ctx: RouteContext): Promise<Response> {
  return proxy(request, ctx);
}
