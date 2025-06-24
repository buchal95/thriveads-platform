import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  webpack: (config, { isServer }) => {
    // Ensure webpack resolves the @ alias properly
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.join(__dirname, 'src'),
      '@/components': path.join(__dirname, 'src', 'components'),
      '@/lib': path.join(__dirname, 'src', 'lib'),
      '@/data': path.join(__dirname, 'src', 'data'),
      '@/types': path.join(__dirname, 'src', 'types'),
      '@/services': path.join(__dirname, 'src', 'services'),
      '@/config': path.join(__dirname, 'src', 'config'),
    };

    // Debug logging
    if (!isServer) {
      console.log('Webpack aliases:', config.resolve.alias);
    }

    return config;
  },
};

export default nextConfig;
