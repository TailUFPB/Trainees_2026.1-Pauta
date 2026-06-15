import { CandidatosNav } from "./CandidatosNav";

// Hub de Candidatos: agrega o catálogo de vereadores e as recomendações por
// afinidade sob uma sub-navegação em abas, espelhando a estrutura da conta.
export default function CandidatosLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col">
      <CandidatosNav />
      {children}
    </div>
  );
}
