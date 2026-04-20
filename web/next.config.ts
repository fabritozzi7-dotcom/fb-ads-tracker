import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { hostname: "scontent.fmvd2-1.fna.fbcdn.net" },
      { hostname: "**.fbcdn.net" },
    ],
  },
};

export default nextConfig;
