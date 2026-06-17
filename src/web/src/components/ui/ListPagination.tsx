import { Pagination } from "antd";

interface ListPaginationProps {
  current: number;
  total: number;
  pageSize?: number;
  onChange: (page: number) => void;
}

/** 统一分页容器 */
export default function ListPagination({
  current,
  total,
  pageSize = 20,
  onChange,
}: ListPaginationProps) {
  if (total <= pageSize) return null;

  return (
    <div className="text-center mt-4">
      <Pagination
        current={current}
        total={total}
        pageSize={pageSize}
        onChange={onChange}
        showSizeChanger={false}
      />
    </div>
  );
}
