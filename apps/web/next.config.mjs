/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@sellscope/shared"],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "stock.adobe.com",
      },
      {
        protocol: "https",
        hostname: "*.ftcdn.net",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: process.env.NEXT_PUBLIC_API_URL
          ? `${process.env.NEXT_PUBLIC_API_URL}/:path*`
          : "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
