"use client";

import "leaflet/dist/leaflet.css";
import { CircleMarker, MapContainer, TileLayer } from "react-leaflet";

// Mini-mapa estático centrado no problema — sem interação por scroll, apenas
// referência visual da localização. Cor accent do projeto: #ff6b35.
export function MiniMapa({ lat, lng }: { lat: number; lng: number }) {
  return (
    <div className="overflow-hidden rounded-md border border-border">
      <MapContainer
        center={[lat, lng]}
        zoom={16}
        scrollWheelZoom={false}
        style={{ height: "16rem", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; CARTO'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
        />
        <CircleMarker
          center={[lat, lng]}
          radius={10}
          pathOptions={{
            color: "#ff6b35",
            fillColor: "#ff6b35",
            fillOpacity: 0.7,
          }}
        />
      </MapContainer>
    </div>
  );
}
