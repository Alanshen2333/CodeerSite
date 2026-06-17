"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, Button, Space, Input, Typography, message, Popconfirm } from "antd";
import { PlusOutlined, DeleteOutlined, ArrowRightOutlined } from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getColumns, createColumn, deleteColumn, createCard, deleteCard, moveCard } from "@/lib/api/kanban";
import type { KanbanColumn, KanbanCard as KanbanCardType } from "@/types";
import Link from "next/link";
import LoadingState from "@/components/ui/LoadingState";

const { Text } = Typography;

export default function KanbanPage() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const [columns, setColumns] = useState<KanbanColumn[]>([]);
  const [loading, setLoading] = useState(true);
  const [newColTitle, setNewColTitle] = useState("");
  const [newCardTitles, setNewCardTitles] = useState<Record<string, string>>({});

  const fetch = async () => {
    try {
      const r = await getColumns(slug);
      setColumns(r.columns);
    } catch {
      setColumns([]);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    fetch();
  }, [slug]);

  const addColumn = async () => {
    if (!newColTitle.trim()) return;
    try {
      await createColumn(slug, newColTitle.trim());
      setNewColTitle("");
      fetch();
    } catch {
      message.error("添加列失败");
    }
  };

  const handleDeleteColumn = async (colId: string) => {
    try {
      await deleteColumn(slug, colId);
      fetch();
    } catch {
      message.error("删除列失败");
    }
  };

  const addCard = async (colId: string) => {
    const title = newCardTitles[colId]?.trim();
    if (!title) return;
    try {
      await createCard(slug, colId, { title });
      setNewCardTitles((p) => ({ ...p, [colId]: "" }));
      fetch();
    } catch {
      message.error("添加卡片失败");
    }
  };

  const handleDeleteCard = async (cardId: string) => {
    try {
      await deleteCard(slug, cardId);
      fetch();
    } catch {
      message.error("删除卡片失败");
    }
  };

  const handleMoveRight = async (card: KanbanCardType, colIdx: number) => {
    if (colIdx >= columns.length - 1) return;
    const targetCol = columns[colIdx + 1];
    try {
      await moveCard(slug, card.id, { column_id: targetCol.id, position: 0 });
      fetch();
    } catch {
      message.error("移动失败");
    }
  };

  if (loading) return <LoadingState size="large" />;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-text m-0">看板</h2>
        <Link href={`/projects/${slug}`}>
          <Button>返回项目</Button>
        </Link>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4 min-h-[300px]">
        {columns.map((col, idx) => (
          <Card
            key={col.id}
            title={<Text strong>{col.title}</Text>}
            extra={
              <Popconfirm title="删除此列？" onConfirm={() => handleDeleteColumn(col.id)}>
                <Button type="text" danger size="small" icon={<DeleteOutlined />} />
              </Popconfirm>
            }
            className="min-w-[260px] max-w-[300px] shrink-0"
            styles={{ body: { padding: "12px" } }}
          >
            {col.cards?.map((card) => (
              <Card key={card.id} size="small" className="mb-2" hoverable>
                <div className="flex justify-between items-center">
                  <span className="flex-1 text-xs">{card.title}</span>
                  <Space size={4}>
                    {idx < columns.length - 1 && (
                      <Button
                        type="text"
                        size="small"
                        icon={<ArrowRightOutlined />}
                        onClick={() => handleMoveRight(card, idx)}
                      />
                    )}
                    <Button
                      type="text"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={() => handleDeleteCard(card.id)}
                    />
                  </Space>
                </div>
                {card.issue && (
                  <Link
                    href={`/projects/${slug}/issues/${card.issue.issue_number}`}
                    className="text-xs"
                  >
                    #{card.issue.issue_number} {card.issue.title}
                  </Link>
                )}
              </Card>
            ))}
            <Space.Compact className="w-full">
              <Input
                size="small"
                placeholder="新卡片..."
                value={newCardTitles[col.id] || ""}
                onChange={(e) =>
                  setNewCardTitles((p) => ({ ...p, [col.id]: e.target.value }))
                }
                onPressEnter={() => addCard(col.id)}
              />
              <Button
                size="small"
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => addCard(col.id)}
              />
            </Space.Compact>
          </Card>
        ))}

        {/* Add column */}
        <Card
          className="min-w-[200px] max-w-[220px] shrink-0"
          styles={{ body: { padding: "12px" } }}
        >
          <Space orientation="vertical" className="w-full">
            <Input
              placeholder="列名称..."
              value={newColTitle}
              onChange={(e) => setNewColTitle(e.target.value)}
              onPressEnter={addColumn}
            />
            <Button block icon={<PlusOutlined />} onClick={addColumn}>
              添加列
            </Button>
          </Space>
        </Card>
      </div>
    </div>
  );
}
