"use client";

import { useState, useEffect } from "react";
import { Button, Space, Input, Typography, Popconfirm } from "antd";
import { message } from "@/lib/message";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import { DragDropContext, Droppable, Draggable, type DropResult } from "@hello-pangea/dnd";
import {
  getColumns,
  createColumn,
  deleteColumn,
  createCard,
  deleteCard,
  moveCard,
  reorderColumns,
} from "@/lib/api/kanban";
import type { KanbanColumn } from "@/types";
import LoadingState from "@/components/ui/LoadingState";

const { Text } = Typography;

interface Props {
  slug: string;
  /** 点击关联 Issue 的卡片回调（打开 Issue 抽屉） */
  onOpenIssue: (issueNumber: number) => void;
  /** 抽屉内变更后递增，触发看板刷新（卡片关联 issue 状态可能变化） */
  refreshTick?: number;
}

/** 看板面板 —— 拖拽逻辑迁自独立 kanban 页。 */
export default function KanbanPanel({ slug, onOpenIssue, refreshTick }: Props) {
  const [columns, setColumns] = useState<KanbanColumn[]>([]);
  const [loading, setLoading] = useState(true);
  const [newColTitle, setNewColTitle] = useState("");
  const [newCardTitles, setNewCardTitles] = useState<Record<string, string>>({});

  const loadColumns = async () => {
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
    loadColumns();
  }, [slug, refreshTick]);

  const addColumn = async () => {
    if (!newColTitle.trim()) return;
    try {
      await createColumn(slug, newColTitle.trim());
      setNewColTitle("");
      loadColumns();
    } catch {
      message.error("添加列失败");
    }
  };

  const handleDeleteColumn = async (colId: string) => {
    try {
      await deleteColumn(slug, colId);
      loadColumns();
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
      loadColumns();
    } catch {
      message.error("添加卡片失败");
    }
  };

  const handleDeleteCard = async (cardId: string) => {
    try {
      await deleteCard(slug, cardId);
      loadColumns();
    } catch {
      message.error("删除卡片失败");
    }
  };

  // 拖拽结束：卡片跨列/同列移动、列整体重排。乐观更新本地状态，失败回滚。
  const onDragEnd = (result: DropResult) => {
    const { source, destination, type } = result;
    if (!destination) return;
    if (source.droppableId === destination.droppableId && source.index === destination.index) {
      return;
    }

    const snapshot = columns; // 回滚用

    if (type === "card") {
      setColumns((cols) => {
        const next = cols.map((c) => ({ ...c, cards: [...(c.cards ?? [])] }));
        const fromCol = next.find((c) => c.id === source.droppableId);
        const toCol = next.find((c) => c.id === destination.droppableId);
        if (!fromCol || !toCol || !fromCol.cards) return cols;
        const [moved] = fromCol.cards.splice(source.index, 1);
        toCol.cards = toCol.cards ?? [];
        toCol.cards.splice(destination.index, 0, moved);
        return next;
      });

      const fromCol = snapshot.find((c) => c.id === source.droppableId);
      const movedCard = fromCol?.cards?.[source.index];
      if (!movedCard) return;
      moveCard(slug, movedCard.id, {
        column_id: destination.droppableId,
        position: destination.index,
      }).catch(() => {
        setColumns(snapshot);
        message.error("移动失败，已还原");
      });
    } else {
      const reordered = [...snapshot];
      const [moved] = reordered.splice(source.index, 1);
      reordered.splice(destination.index, 0, moved);
      setColumns(reordered);

      reorderColumns(slug, reordered.map((c) => c.id)).catch(() => {
        setColumns(snapshot);
        message.error("排序失败，已还原");
      });
    }
  };

  if (loading) return <LoadingState size="large" />;

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Droppable droppableId="board" type="column" direction="horizontal">
        {(provided) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className="flex gap-4 overflow-x-auto pb-4 min-h-[300px]"
          >
            {columns.map((col, colIdx) => (
              <Draggable key={col.id} draggableId={col.id} index={colIdx}>
                {(dragProvided) => (
                  <div
                    ref={dragProvided.innerRef}
                    {...dragProvided.draggableProps}
                    className="min-w-[260px] max-w-[300px] shrink-0 flex flex-col bg-bg-container border border-border rounded-lg"
                  >
                    {/* 列头 —— 整列拖动手柄 */}
                    <div
                      {...dragProvided.dragHandleProps}
                      className="flex justify-between items-center px-3 py-2 border-b border-border cursor-grab active:cursor-grabbing"
                    >
                      <Text strong className="text-text">{col.title}</Text>
                      <Popconfirm title="删除此列？" onConfirm={() => handleDeleteColumn(col.id)}>
                        <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                      </Popconfirm>
                    </div>

                    {/* 卡片区 */}
                    <Droppable droppableId={col.id} type="card">
                      {(dropProvided) => (
                        <div
                          ref={dropProvided.innerRef}
                          {...dropProvided.droppableProps}
                          className="flex flex-col gap-2 p-3 min-h-[40px] flex-1"
                        >
                          {col.cards?.map((card, cardIdx) => (
                            <Draggable key={card.id} draggableId={card.id} index={cardIdx}>
                              {(cardProvided) => (
                                <div
                                  ref={cardProvided.innerRef}
                                  {...cardProvided.draggableProps}
                                  {...cardProvided.dragHandleProps}
                                  className="bg-bg-elevated border border-border rounded p-2 hover:shadow-sm transition-shadow"
                                >
                                  <div className="flex justify-between items-center gap-2">
                                    <span className="flex-1 text-xs text-text break-words">{card.title}</span>
                                    <Button
                                      type="text"
                                      danger
                                      size="small"
                                      icon={<DeleteOutlined />}
                                      onClick={() => handleDeleteCard(card.id)}
                                    />
                                  </div>
                                  {card.issue && (
                                    <button
                                      type="button"
                                      onClick={() => onOpenIssue(card.issue!.issue_number)}
                                      className="text-xs text-primary hover:underline text-left"
                                    >
                                      #{card.issue.issue_number} {card.issue.title}
                                    </button>
                                  )}
                                </div>
                              )}
                            </Draggable>
                          ))}
                          {dropProvided.placeholder}
                        </div>
                      )}
                    </Droppable>

                    {/* 新建卡片 */}
                    <div className="p-3 pt-0">
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
                    </div>
                  </div>
                )}
              </Draggable>
            ))}

            {/* 添加列 */}
            <div className="min-w-[200px] max-w-[220px] shrink-0 bg-bg-container border border-border rounded-lg p-3">
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
            </div>

            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
}
