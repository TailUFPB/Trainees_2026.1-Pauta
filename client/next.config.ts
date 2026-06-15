import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  productionBrowserSourceMaps: false,
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "sapl.bayeux.pb.leg.br" },
      { protocol: "https", hostname: "joaopessoa.pb.leg.br" },
      { protocol: "https", hostname: "ui-avatars.com" },
      { protocol: "https", hostname: "www.camaracg.pb.gov.br" },
      { protocol: "https", hostname: "www.santarita.pb.leg.br" },
    ],
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=(self)",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
