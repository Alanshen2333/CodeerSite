import type { ReactNode } from "react";
import { Typography, Breadcrumb, Space } from "antd";

const { Title, Text } = Typography;

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  breadcrumb?: BreadcrumbItem[];
  className?: string;
}

/** 页面标题栏 — 标题 + 操作按钮 + 面包屑 */
export default function PageHeader({
  title,
  subtitle,
  actions,
  breadcrumb,
  className = "",
}: PageHeaderProps) {
  return (
    <div className={className}>
      {breadcrumb && breadcrumb.length > 0 && (
        <Breadcrumb
          className="mb-2"
          items={breadcrumb.map((item) => ({
            title: item.href ? <a href={item.href}>{item.label}</a> : item.label,
          }))}
        />
      )}
      <div className="flex justify-between items-center flex-wrap gap-3 mb-6">
        <div className="min-w-0">
          <Title level={4} className="!mb-0">
            {title}
          </Title>
          {subtitle && (
            <Text type="secondary" className="text-sm mt-1 block">
              {subtitle}
            </Text>
          )}
        </div>
        {actions && <Space wrap>{actions}</Space>}
      </div>
    </div>
  );
}
