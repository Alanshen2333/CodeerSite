import { expect, test, type Page } from "@playwright/test";
import { themePalettes, type Theme } from "../../src/styles/tokens";

const cssPaletteVariables = {
  primary: "--tw-color-primary",
  primaryHover: "--tw-color-primary-hover",
  success: "--tw-color-success",
  warning: "--tw-color-warning",
  error: "--tw-color-error",
  info: "--tw-color-info",
  link: "--tw-color-link",
  bgLayout: "--tw-color-bg-layout",
  bgContainer: "--tw-color-bg-container",
  bgElevated: "--tw-color-bg-elevated",
  border: "--tw-color-border",
  borderSecondary: "--tw-color-border-secondary",
  text: "--tw-color-text",
  textSecondary: "--tw-color-text-secondary",
  textTertiary: "--tw-color-text-tertiary",
  textDisabled: "--tw-color-text-disabled",
  glowPrimary: "--tw-glow-primary",
  glowSecondary: "--tw-glow-secondary",
  gridLine: "--tw-grid-line",
  bgGlass: "--tw-color-bg-glass",
  borderGlass: "--tw-color-border-glass",
  borderHover: "--tw-color-border-hover",
} as const;

async function mockHomeApi(page: Page) {
  await page.route("**/api/stats", (route) =>
    route.fulfill({ json: { questions: 2, answers: 1, projects: 3, users: 4 } }),
  );
  await page.route("**/api/questions?**", (route) =>
    route.fulfill({ json: { questions: [], total: 0, pages: 0, current_page: 1 } }),
  );
}

test("首次访问在系统深色下呈现统一的暗色表面", async ({ browser }) => {
  const context = await browser.newContext({ colorScheme: "dark" });
  const page = await context.newPage();
  await mockHomeApi(page);

  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Codeersite" })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  await expect
    .poll(() => page.locator(".glass-card").first().evaluate((element) => getComputedStyle(element).backgroundColor))
    .toBe("rgba(22, 22, 29, 0.55)");

  const colors = await page.evaluate(() => ({
    body: getComputedStyle(document.body).backgroundColor,
    card: getComputedStyle(document.querySelector(".glass-card")!).backgroundColor,
    cardText: getComputedStyle(document.querySelector(".glass-card")!).color,
  }));

  expect(colors).toEqual({
    body: "rgb(13, 13, 18)",
    card: "rgba(22, 22, 29, 0.55)",
    cardText: "rgb(237, 237, 240)",
  });

  await context.close();
});

test("用户切换主题后刷新仍保留选择", async ({ browser }) => {
  const context = await browser.newContext({ colorScheme: "dark" });
  const page = await context.newPage();
  await mockHomeApi(page);

  await page.goto("/");
  await page.getByRole("button", { name: "切换到浅色模式" }).click();

  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("button", { name: "切换到深色模式" })).toBeVisible();

  await context.close();
});

test("未设置偏好时跟随系统，手动切换后停止跟随", async ({ browser }) => {
  const context = await browser.newContext({ colorScheme: "light" });
  const page = await context.newPage();
  await mockHomeApi(page);

  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  await page.getByRole("button", { name: "切换到浅色模式" }).click();
  await page.emulateMedia({ colorScheme: "light" });
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

  await context.close();
});

test("同一浏览器的标签页同步用户主题选择", async ({ browser }) => {
  const context = await browser.newContext({ colorScheme: "light" });
  const firstPage = await context.newPage();
  const secondPage = await context.newPage();
  await mockHomeApi(firstPage);
  await mockHomeApi(secondPage);

  await Promise.all([firstPage.goto("/"), secondPage.goto("/")]);
  await expect(secondPage.locator("html")).toHaveAttribute("data-theme-ready", "true");
  await firstPage.getByRole("button", { name: "切换到深色模式" }).click();

  await expect(secondPage.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(secondPage.getByRole("button", { name: "切换到浅色模式" })).toBeVisible();

  await context.close();
});

for (const theme of ["light", "dark"] satisfies Theme[]) {
  test(`${theme} 的 CSS 变量与 TypeScript Palette 一致`, async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await mockHomeApi(page);
    await page.addInitScript((value) => localStorage.setItem("theme", value), theme);
    await page.goto("/");

    const actual = await page.evaluate((variables) => {
      const probe = document.createElement("span");
      document.body.append(probe);
      const result: Record<string, string> = {};
      for (const [key, variable] of Object.entries(variables)) {
        probe.style.color = `var(${variable})`;
        result[key] = getComputedStyle(probe).color;
      }
      probe.remove();
      return result;
    }, cssPaletteVariables);

    const expected = await page.evaluate((palette) => {
      const probe = document.createElement("span");
      document.body.append(probe);
      const result: Record<string, string> = {};
      for (const [key, color] of Object.entries(palette)) {
        probe.style.color = color;
        result[key] = getComputedStyle(probe).color;
      }
      probe.remove();
      return result;
    }, themePalettes[theme]);

    expect(actual).toEqual(expected);
    await context.close();
  });
}

test("暗色下 AntD 按钮和浮层保持可读且无 hydration 错误", async ({ browser }) => {
  const context = await browser.newContext({ colorScheme: "dark" });
  const page = await context.newPage();
  const runtimeErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") runtimeErrors.push(message.text());
  });
  page.on("pageerror", (error) => runtimeErrors.push(error.message));
  await mockHomeApi(page);

  await page.goto("/");
  const defaultButton = page.getByRole("button", { name: "浏览问答" });
  await expect(defaultButton).toBeVisible();
  await expect
    .poll(() => defaultButton.evaluate((element) => getComputedStyle(element).backgroundColor))
    .toBe("rgb(22, 22, 29)");

  await page.getByRole("button", { name: "切换到浅色模式" }).hover();
  const tooltip = page.getByRole("tooltip");
  await expect(tooltip).toBeVisible();
  const tooltipColors = await tooltip.evaluate((element) => {
    const content = element.querySelector(".ant-tooltip-inner") ?? element;
    const style = getComputedStyle(content);
    return { background: style.backgroundColor, text: style.color };
  });
  expect(tooltipColors.background).not.toBe("rgb(255, 255, 255)");
  expect(tooltipColors.text).not.toBe("rgb(26, 26, 46)");
  expect(runtimeErrors).toEqual([]);

  await context.close();
});

test("窄屏下主题导航不会造成横向溢出", async ({ browser }) => {
  const context = await browser.newContext({
    colorScheme: "dark",
    viewport: { width: 390, height: 844 },
  });
  const page = await context.newPage();
  await mockHomeApi(page);

  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect
    .poll(() =>
      page.evaluate(() => ({
        viewport: document.documentElement.clientWidth,
        content: document.documentElement.scrollWidth,
      })),
    )
    .toEqual({ viewport: 390, content: 390 });

  await context.close();
});

test("系统深色首次绘制时 CSS 与 AntD 表面已经一致", async ({ browser }) => {
  const context = await browser.newContext({ colorScheme: "dark" });
  const page = await context.newPage();
  await mockHomeApi(page);
  await page.addInitScript(() => {
    const frames: Array<{ body: string; card: string }> = [];
    Object.assign(window, { __themeFrames: frames });
    const sample = () => {
      const card = document.querySelector(".glass-card");
      if (card && document.documentElement.dataset.themeReady === "true") {
        frames.push({
          body: getComputedStyle(document.body).backgroundColor,
          card: getComputedStyle(card).backgroundColor,
        });
      }
      if (frames.length < 3) requestAnimationFrame(sample);
    };
    requestAnimationFrame(sample);
  });

  await page.goto("/");
  await expect
    .poll(() =>
      page.evaluate(
        () =>
          (window as typeof window & { __themeFrames?: Array<{ body: string; card: string }> })
            .__themeFrames?.length ?? 0,
      ),
    )
    .toBeGreaterThanOrEqual(1);

  const firstFrame = await page.evaluate(
    () =>
      (window as typeof window & { __themeFrames: Array<{ body: string; card: string }> })
        .__themeFrames[0],
  );
  expect(firstFrame).toEqual({
    body: "rgb(13, 13, 18)",
    card: "rgba(22, 22, 29, 0.55)",
  });

  await context.close();
});
