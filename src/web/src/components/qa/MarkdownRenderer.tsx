"use client";

interface MarkdownRendererProps {
  html: string;
}

export default function MarkdownRenderer({ html }: MarkdownRendererProps) {
  return (
    <div
      className="markdown-body break-words leading-relaxed text-[15px]"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
