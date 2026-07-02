"use client";

import { useEffect } from "react";
import { Modal, Input, Form, DatePicker, Space, Button } from "antd";
import { message } from "@/lib/message";
import { createMilestone, updateMilestone } from "@/lib/api/milestones";
import type { Milestone } from "@/types";
import dayjs from "dayjs";

interface FormValues {
  title: string;
  description?: string;
  due_date?: dayjs.Dayjs | null;
}

interface Props {
  slug: string;
  open: boolean;
  /** 传入里程碑则为编辑模式，否则新建 */
  milestone?: Milestone | null;
  onClose: () => void;
  onSaved?: () => void;
}

/** 里程碑新建/编辑共用表单 Modal。后端 create/update 均支持 description/due_date。 */
export default function MilestoneFormModal({ slug, open, milestone, onClose, onSaved }: Props) {
  const [form] = Form.useForm<FormValues>();
  const isEdit = !!milestone;

  useEffect(() => {
    if (!open) return;
    form.setFieldsValue({
      title: milestone?.title ?? "",
      description: milestone?.description ?? "",
      due_date: milestone?.due_date ? dayjs(milestone.due_date) : null,
    });
  }, [open, milestone, form]);

  const onFinish = async (values: FormValues) => {
    try {
      const payload = {
        title: values.title.trim(),
        description: values.description || undefined,
        due_date: values.due_date ? values.due_date.format("YYYY-MM-DD") : null,
      };
      if (isEdit && milestone) {
        await updateMilestone(slug, milestone.id, payload);
        message.success("已保存");
      } else {
        await createMilestone(slug, {
          title: payload.title,
          description: payload.description,
          due_date: payload.due_date || undefined,
        });
        message.success("已创建");
      }
      onSaved?.();
      onClose();
    } catch {
      message.error(isEdit ? "保存失败" : "创建失败");
    }
  };

  return (
    <Modal
      open={open}
      title={isEdit ? "编辑里程碑" : "新建里程碑"}
      onCancel={onClose}
      destroyOnHidden
      footer={null}
    >
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item
          name="title"
          label="名称"
          rules={[{ required: true, message: "请输入名称" }, { max: 200 }]}
        >
          <Input placeholder="如 v1.0" />
        </Form.Item>
        <Form.Item name="description" label="描述">
          <Input.TextArea rows={3} placeholder="里程碑目标与范围..." />
        </Form.Item>
        <Form.Item name="due_date" label="截止日期">
          <DatePicker className="w-full" placeholder="选填" />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              {isEdit ? "保存" : "创建"}
            </Button>
            <Button onClick={onClose}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
}
