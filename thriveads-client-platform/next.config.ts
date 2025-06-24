import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  webpack: (config) => {
    // Ensure webpack resolves the @ alias properly
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, 'src'),
      '@/components': path.resolve(__dirname, 'src/components'),
      '@/lib': path.resolve(__dirname, 'src/lib'),
      '@/data': path.resolve(__dirname, 'src/data'),
      '@/types': path.resolve(__dirname, 'src/types'),
      '@/services': path.resolve(__dirname, 'src/services'),
    };
    return config;
  },
};

export default nextConfig;
