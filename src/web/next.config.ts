import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["antd", "@ant-design/icons", "@ant-design/nextjs-registry"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        // 5100：避开 macOS AirPlay 接收器占用的 5000 端口（与 scripts/dev.sh 同步）
        destination: "http://127.0.0.1:5100/api/:path*",
      },
    ];
  },
};

export default nextConfig;
