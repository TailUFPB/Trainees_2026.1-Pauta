"use client";

import dynamic from "next/dynamic";

// Leaflet acessa `window`, então o mapa só carrega no client (ssr desligado).
const MapaProblemas = dynamic(() => import("./MapaProblemas"), {
  ssr: false,
  loading: () => <p className="text-sm text-zinc-500">Carregando mapa…</p>,
});

export default function MapaPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Mapa de problemas</h1>
        <p className="text-sm text-zinc-600">
          Mova o mapa para carregar os problemas reportados na região visível.
        </p>
      </div>
      <MapaProblemas />
    </div>
  );
}
