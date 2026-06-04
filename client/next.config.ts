import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "sapl.bayeux.pb.leg.br" },
      { protocol: "https", hostname: "joaopessoa.pb.leg.br" },
      { protocol: "https", hostname: "ui-avatars.com" },
      { protocol: "https", hostname: "www.camaracg.pb.gov.br" },
      { protocol: "https", hostname: "www.santarita.pb.leg.br" },
    ],
  },
};

export default nextConfig;
