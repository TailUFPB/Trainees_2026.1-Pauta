"use client";

import "leaflet/dist/leaflet.css";
import type { Map as LeafletMap } from "leaflet";
import { useCallback, useEffect, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMapEvents } from "react-leaflet";
import { api } from "@/lib/api/client";
import type { Problema, Severidade } from "@/lib/api/types";

// João Pessoa/PB como centro padrão.
const CENTRO: [number, number] = [-7.115, -34.861];

const COR_SEVERIDADE: Record<Severidade, string> = {
  baixa: "#22c55e",
  media: "#eab308",
  alta: "#f97316",
  critica: "#ef4444",
};

function Carregador({ onDados }: { onDados: (p: Problema[]) => void }) {
  const carregar = useCallback(
    async (map: LeafletMap) => {
      const b = map.getBounds();
      try {
        const dados = await api.listarProblemas([
          b.getWest(),
          b.getSouth(),
          b.getEast(),
          b.getNorth(),
        ]);
        onDados(dados);
      } catch {
        // backend offline / sem sessão — mantém o que já tinha
      }
    },
    [onDados],
  );

  const map = useMapEvents({
    moveend: () => carregar(map),
  });

  // Carrega na montagem inicial.
  useEffect(() => {
    carregar(map);
  }, [map, carregar]);

  return null;
}

export default function MapaProblemas() {
  const [problemas, setProblemas] = useState<Problema[]>([]);

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200">
      <MapContainer center={CENTRO} zoom={13} style={{ height: "70vh", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Carregador onDados={setProblemas} />
        {problemas.map((p) => (
          <CircleMarker
            key={p.id}
            center={[p.lat, p.lng]}
            radius={9}
            pathOptions={{
              color: COR_SEVERIDADE[p.severidade ?? "media"],
              fillColor: COR_SEVERIDADE[p.severidade ?? "media"],
              fillOpacity: 0.7,
            }}
          >
            <Popup>
              <strong>{p.tipo_problema}</strong> — {p.severidade}
              <br />
              {p.resumo_llm}
              <br />
              <em>Status: {p.status}</em>
              {p.precisa_revisao && <div>⚠️ aguardando revisão</div>}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
      <p className="bg-white px-3 py-2 text-xs text-zinc-500">
        {problemas.length} problema(s) na área visível.
      </p>
    </div>
  );
}
