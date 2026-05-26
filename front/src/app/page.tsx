import Link from "next/link";

const cards = [
  {
    href: "/mapa",
    titulo: "Mapa de problemas",
    desc: "Veja problemas de infraestrutura reportados pela população, por região.",
  },
  {
    href: "/reportar",
    titulo: "Reportar um problema",
    desc: "Envie uma foto e a localização. A análise classifica o tipo e a severidade.",
  },
  {
    href: "/recomendacoes",
    titulo: "Candidatos para você",
    desc: "Recomendação de políticos por afinidade com as suas pautas.",
  },
];

export default function Home() {
  return (
    <div className="flex flex-col gap-8">
      <section>
        <h1 className="text-3xl font-semibold tracking-tight">Pauta</h1>
        <p className="mt-2 max-w-xl text-zinc-600">
          Transparência política ligada ao bem-estar municipal: mapeie problemas de
          infraestrutura, acompanhe a resolução e descubra candidatos alinhados às suas pautas.
        </p>
      </section>
      <section className="grid gap-4 sm:grid-cols-3">
        {cards.map((c) => (
          <Link
            key={c.href}
            href={c.href}
            className="rounded-lg border border-zinc-200 bg-white p-5 transition hover:border-zinc-400"
          >
            <h2 className="font-medium">{c.titulo}</h2>
            <p className="mt-1 text-sm text-zinc-600">{c.desc}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}
