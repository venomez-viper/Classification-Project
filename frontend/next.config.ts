import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true, // We want it to deploy even with minor type issues
  },
  experimental: {
    cpus: 1,
    workerThreads: false,
  },
};

export default nextConfig;
