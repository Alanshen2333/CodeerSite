"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, Button, Space, Typography } from "antd";
import { CopyOutlined, DownloadOutlined } from "@ant-design/icons";
import { codeToHtml } from "shiki";
import { useTheme } from "@/providers/ThemeProvider";
import { message } from "@/lib/message";
import type { Blob } from "@/types";

interface BlobViewerProps {
  blob: Blob;
}

function guessLang(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  const map: Record<string, string> = {
    js: "javascript",
    mjs: "javascript",
    cjs: "javascript",
    ts: "typescript",
    tsx: "tsx",
    jsx: "jsx",
    py: "python",
    json: "json",
    yml: "yaml",
    yaml: "yaml",
    md: "markdown",
    mdx: "markdown",
    css: "css",
    scss: "scss",
    less: "less",
    html: "html",
    htm: "html",
    xml: "xml",
    sh: "shellscript",
    bash: "shellscript",
    zsh: "shellscript",
    sql: "sql",
    rs: "rust",
    go: "go",
    java: "java",
    kt: "kotlin",
    swift: "swift",
    c: "c",
    h: "c",
    cpp: "cpp",
    cc: "cpp",
    hpp: "cpp",
    dockerfile: "dockerfile",
    nginx: "nginx",
    toml: "toml",
    ini: "ini",
    env: "ini",
    vue: "vue",
    svelte: "svelte",
    php: "php",
    rb: "ruby",
  };
  return map[ext] || "text";
}

function isBinary(size: number, content: string): boolean {
  if (!content && size > 0) return true;
  return false;
}

export default function BlobViewer({ blob }: BlobViewerProps) {
  const { theme } = useTheme();
  const [html, setHtml] = useState<string | null>(null);
  const [highlighting, setHighlighting] = useState(true);

  const lang = useMemo(() => guessLang(blob.path), [blob.path]);
  const shikiTheme = theme === "dark" ? "github-dark" : "github-light";

  useEffect(() => {
    let cancelled = false;
    setHighlighting(true);
    codeToHtml(blob.content, { lang, theme: shikiTheme })
      .then((h) => {
        if (!cancelled) setHtml(h);
      })
      .catch(() => {
        if (!cancelled) setHtml(null);
      })
      .finally(() => {
        if (!cancelled) setHighlighting(false);
      });
    return () => {
      cancelled = true;
    };
  }, [blob.content, lang, shikiTheme]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(blob.content);
      message.success("已复制");
    } catch {
      message.error("复制失败");
    }
  };

  const handleDownload = () => {
    const a = document.createElement("a");
    const blobData = new Blob([blob.content], { type: "text/plain;charset=utf-8" });
    a.href = URL.createObjectURL(blobData);
    a.download = blob.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
  };

  if (isBinary(blob.size, blob.content)) {
    return (
      <Card className="shadow-sm">
        <EmptyBlob name={blob.name} path={blob.path} size={blob.size}>
          二进制文件，不支持在线预览
        </EmptyBlob>
      </Card>
    );
  }

  return (
    <Card
      className="shadow-sm"
      title={
        <Typography.Text className="text-text font-medium" ellipsis>
          {blob.name}
        </Typography.Text>
      }
      extra={
        <Space>
          <Button icon={<CopyOutlined />} size="small" onClick={handleCopy}>
            复制
          </Button>
          <Button icon={<DownloadOutlined />} size="small" onClick={handleDownload}>
            下载
          </Button>
        </Space>
      }
    >
      {highlighting && !html ? (
        <div className="py-12 text-center text-text-secondary">高亮加载中…</div>
      ) : html ? (
        <div
          className="overflow-x-auto text-sm [&_pre]:m-0 [&_pre]:rounded-lg [&_pre]:p-4"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      ) : (
        <pre className="m-0 overflow-x-auto rounded-lg bg-bg-elevated p-4 text-sm text-text">
          {blob.content}
        </pre>
      )}
    </Card>
  );
}

function EmptyBlob({
  children,
  name,
  path,
  size,
}: {
  children: React.ReactNode;
  name: string;
  path: string;
  size: number;
}) {
  return (
    <div className="py-12 text-center">
      <Typography.Text className="block text-text-secondary">
        {children}
      </Typography.Text>
      <Typography.Text className="mt-2 block text-text-tertiary text-xs">
        {path} · {size} bytes
      </Typography.Text>
    </div>
  );
}
