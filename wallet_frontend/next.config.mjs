/** @type {import('next').NextConfig} */
const nextConfig = {
    images: {
    // Allow local /public images (default) — no remote patterns needed
    unoptimized: false,
  },
  async rewrites() {
    const rawBackendUrl =
      process.env.NEXT_PUBLIC_API_PROXY_URL?.replace(/\/$/, "") ??
      "http://127.0.0.1:8000";

    const backendUrl = rawBackendUrl
      .replace(/^http:\/\/localhost(?=[:/]|$)/, "http://127.0.0.1")
      .replace(/^https:\/\/localhost(?=[:/]|$)/, "https://127.0.0.1");

    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

// /** @type {import('next').NextConfig} */
// const nextConfig = {
//   images: {
//     // Allow local /public images (default) — no remote patterns needed
//     unoptimized: false,
//   },
//   async rewrites() {
//     const backendUrl =
//       process.env.NEXT_PUBLIC_API_PROXY_URL?.replace(/\/$/, "") ??
//       "http://localhost:8000";
//     return [
//       {
//         source: "/api/:path*",
//         destination: `${backendUrl}/api/:path*`,
//       },
//     ];
//   },
// };

// export default nextConfig;