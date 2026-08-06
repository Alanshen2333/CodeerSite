import { theme as antdTheme, type ThemeConfig } from "antd";
import { antdBaseTokens, themePalettes, type Theme } from "@/styles/tokens";

export function createAntdTheme(theme: Theme): ThemeConfig {
  const palette = themePalettes[theme];

  return {
    algorithm: theme === "dark" ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
    token: {
      ...antdBaseTokens,
      colorPrimary: palette.primary,
      colorSuccess: palette.success,
      colorWarning: palette.warning,
      colorError: palette.error,
      colorInfo: palette.info,
      colorLink: palette.link,
      colorBgBase: palette.bgLayout,
      colorTextBase: palette.text,
      colorBgLayout: palette.bgLayout,
      colorBgContainer: palette.bgContainer,
      colorBgElevated: palette.bgElevated,
      colorBorder: palette.border,
      colorBorderSecondary: palette.borderSecondary,
      colorText: palette.text,
      colorTextSecondary: palette.textSecondary,
      colorTextTertiary: palette.textTertiary,
      colorTextDisabled: palette.textDisabled,
    },
  };
}
