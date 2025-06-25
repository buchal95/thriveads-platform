/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // Enable experimental features if needed
  },
  // Ensure webpack resolves aliases properly for Vercel
  webpack: (config, { isServer }) => {
    // Add alias resolution for @ imports
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': require('path').join(__dirname, 'src'),
    };
    
    return config;
  },
};

module.exports = nextConfig;
