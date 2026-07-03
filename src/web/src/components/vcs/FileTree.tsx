"use client";

import { FolderOutlined, FileOutlined } from "@ant-design/icons";
import type { TreeEntry } from "@/types";

interface FileTreeProps {
  entries: TreeEntry[];
  currentPath: string;
  onNavigate: (path: string) => void;
}

export default function FileTree({ entries, currentPath, onNavigate }: FileTreeProps) {
  if (entries.length === 0) {
    return (
      <div className="py-8 text-center text-text-secondary text-sm">
        空目录
      </div>
    );
  }

  return (
    <ul className="m-0 list-none p-0">
      {entries.map((entry) => (
        <li key={entry.sha}>
          <button
            type="button"
            onClick={() => onNavigate(entry.path)}
            className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-text transition-colors hover:bg-bg-elevated"
          >
            {entry.type === "dir" ? (
              <FolderOutlined className="text-warning" />
            ) : (
              <FileOutlined className="text-text-tertiary" />
            )}
            <span className="truncate">{entry.name}</span>
            {entry.type === "file" && entry.size !== null && (
              <span className="ml-auto text-xs text-text-tertiary">
                {formatSize(entry.size)}
              </span>
            )}
          </button>
        </li>
      ))}
    </ul>
  );
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
