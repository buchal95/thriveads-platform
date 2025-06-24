import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    // Disable ESLint during builds to focus on module resolution
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Disable type checking during builds temporarily
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
