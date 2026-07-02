"use client";

import { App } from "antd";
import { useEffect } from "react";
import { setMessageInstance } from "@/lib/message";

/**
 * 在 antd <App> 内部捕获 hook 实例并注入到 message shim。
 * 必须渲染在 <App> 内部，使 useApp() 返回携带主题上下文的实例。
 */
export default function MessageBridge() {
  const { message } = App.useApp();

  useEffect(() => {
    setMessageInstance(message);
    return () => {
      // 卸载时清空，避免持有过期实例
      setMessageInstance(null);
    };
  }, [message]);

  return null;
}