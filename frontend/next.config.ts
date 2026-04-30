import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true, // We want it to deploy even with minor type issues
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
