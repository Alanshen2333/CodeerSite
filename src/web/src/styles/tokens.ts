/**
 * Codeersite Design Tokens
 *
 * 设计 Token 唯一定义源 —— 同时供给 Tailwind CSS v4 @theme 和 Ant Design ConfigProvider。
 * 修改此文件即可全局生效。注意保持与 globals.css 中 @theme 块同步。
 *
 * 风格参考：Linear / Notion / Vercel Dashboard
 * - 克制的主色
 * - 大量留白
 * - 1px 细边框
 * - 微阴影
 * - 系统字体栈
 */

// ── 品牌色 ────────────────────────────────────────────
export const colors = {
  primary: "#5e6ad2",
  success: "#0eb478",
  warning: "#f5a623",
  error: "#e5484d",
  info: "#5e6ad2",
  link: "#5e6ad2",
} as const;

// ── 中性色（浅色主题） ──────────────────────────────
export const neutral = {
  bgLayout: "#fbfbfc",
  bgContainer: "#ffffff",
  bgElevated: "#ffffff",
  border: "#e8e8ec",
  borderSecondary: "#f0f0f2",
} as const;

// ── 文本色 ─────────────────────────────────────────────
export const text = {
  primary: "#1a1a2e",
  secondary: "#6b6b7b",
  tertiary: "#9b9bae",
  disabled: "#c2c2cc",
} as const;

// ── 深色主题中性色 ──────────────────────────────────
export const darkNeutral = {
  bgLayout: "#0d0d12",
  bgContainer: "#16161d",
  bgElevated: "#1e1e26",
  border: "#2a2a35",
  borderSecondary: "#1e1e28",
} as const;

export const darkText = {
  primary: "#ededf0",
  secondary: "#9b9bae",
  tertiary: "#6b6b7b",
  disabled: "#4a4a55",
} as const;

// ── 圆角 ────────────────────────────────────────────────
export const radius = {
  none: 0,
  xs: 4,
  sm: 6,
  md: 8, // 按钮、输入框
  lg: 12, // 卡片
  xl: 16, // 模态框
  full: 9999,
} as const;

// ── 间距（4px 网格） ─────────────────────────────────
export const spacing = {
  0: 0,
  1: 4,
  2: 8,
  3: 12,
  4: 16,
  5: 20,
  6: 24,
  8: 32,
  10: 40,
  12: 48,
  16: 64,
  20: 80,
} as const;

// ── 排版 ────────────────────────────────────────────────
export const typography = {
  fontFamily:
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
  fontFamilyCode:
    '"SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace',
  // 字号层级
  fontSizeXS: 12,
  fontSizeSM: 13,
  fontSize: 14,
  fontSizeMD: 15,
  fontSizeLG: 16,
  fontSizeXL: 20,
  fontSize2XL: 24,
  fontSize3XL: 32,
  fontSize4XL: 48,
  // 行高
  lineHeightTight: 1.25,
  lineHeight: 1.5,
  lineHeightRelaxed: 1.7,
  // 字重
  fontWeightNormal: 400,
  fontWeightMedium: 500,
  fontWeightSemibold: 600,
  fontWeightBold: 700,
} as const;

// ── 阴影 ────────────────────────────────────────────────
export const shadows = {
  none: "none",
  xs: "0 1px 2px rgba(0,0,0,0.04)",
  sm: "0 1px 2px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.06)",
  md: "0 2px 8px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
  lg: "0 4px 12px rgba(0,0,0,0.08)",
  xl: "0 8px 30px rgba(0,0,0,0.12)",
} as const;

// ── 动画 ────────────────────────────────────────────────
export const motion = {
  durationFast: 100,
  duration: 200,
  durationSlow: 300,
  easeOut: "cubic-bezier(0.16, 1, 0.3, 1)",
  easeInOut: "cubic-bezier(0.65, 0, 0.35, 1)",
} as const;

// ── 布局 ────────────────────────────────────────────────
export const layout = {
  navHeight: 56,
  contentWide: 960,
  contentDefault: 800,
  contentNarrow: 640,
} as const;

// ── z-index ─────────────────────────────────────────────
export const zIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 100,
  modal: 1050,
  toast: 1100,
  tooltip: 1200,
} as const;

// ── Ant Design ConfigProvider theme 配置 ─────────────
// 可直接解构传入 ConfigProvider 的 theme.token
export const antdThemeTokens = {
  // 品牌色
  colorPrimary: colors.primary,
  colorSuccess: colors.success,
  colorWarning: colors.warning,
  colorError: colors.error,
  colorInfo: colors.info,
  colorLink: colors.link,

  // 中性色
  colorBgBase: "#ffffff",
  colorTextBase: text.primary,

  // 字体
  fontFamily: typography.fontFamily,
  fontFamilyCode: typography.fontFamilyCode,
  fontSize: typography.fontSize,

  // 圆角
  borderRadius: radius.md,
  borderRadiusLG: radius.lg,
  borderRadiusSM: radius.sm,
  borderRadiusXS: radius.xs,

  // 线宽
  lineWidth: 1,
  lineType: "solid",

  // 控件高度
  controlHeight: 36,
  sizeUnit: 4,
  sizeStep: 4,

  // 动画
  motionUnit: 0.1,
  motionBase: 0,
  motionEaseOutCirc: motion.easeOut,
  motionEaseInOutCirc: motion.easeInOut,

  // 线框模式关闭
  wireframe: false,
} as const;
