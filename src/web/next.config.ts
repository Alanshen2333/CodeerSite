import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // 生产小规格服务器不做运行时图片转码，也避免运行镜像携带原生 sharp 模块。
  images: { unoptimized: true },
  transpilePackages: ["antd", "@ant-design/icons", "@ant-design/nextjs-registry"],
  allowedDevOrigins: ["127.0.0.1"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        // 5100：避开 macOS AirPlay 接收器占用的 5000 端口（与 scripts/dev.sh 同步）
        destination: `${process.env.API_PROXY_TARGET ?? "http://127.0.0.1:5100"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
