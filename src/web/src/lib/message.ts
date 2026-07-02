/**
 * antd `message` 全局桥接 shim。
 *
 * antd 6 的静态 message.success/error/...无法消费 ConfigProvider 主题上下文，
 * 会触发 "Static function can not consume context like dynamic theme" 警告。
 * 这里通过 <App> + MessageBridge 在运行时捕获 hook 实例，并代理所有调用，
 * 使现有 `message.xxx(...)` 调用点无需改动即可拿到主题上下文。
 */
import { App, message as staticMessage } from "antd";

/** antd useApp() 返回的 message 实例类型。 */
type MessageApi = ReturnType<typeof App.useApp>["message"];

let instance: MessageApi | null = null;

/** 由 MessageBridge 在挂载时注入 hook 实例。 */
export function setMessageInstance(api: MessageApi | null) {
  instance = api;
}

function delegate<K extends keyof MessageApi>(method: K) {
  return (...args: Parameters<MessageApi[K]>) => {
    // 桥接尚未就绪（极早期渲染）时退回静态方法，保证不丢提示。
    const target = (instance ?? staticMessage) as unknown as Record<
      string,
      (...a: Parameters<MessageApi[K]>) => ReturnType<MessageApi[K]>
    >;
    return target[method](...args);
  };
}

export const message = {
  success: delegate("success"),
  error: delegate("error"),
  info: delegate("info"),
  warning: delegate("warning"),
  loading: delegate("loading"),
  open: delegate("open"),
  destroy: delegate("destroy"),
} as MessageApi;