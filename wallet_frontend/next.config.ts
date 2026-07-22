import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Allow local /public images (default) — no remote patterns needed
    unoptimized: false,
  },
  async rewrites() {
    const backendUrl =
      process.env.NEXT_PUBLIC_API_PROXY_URL?.replace(/\/$/, "") ??
      "http://localhost:8000";

    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;


