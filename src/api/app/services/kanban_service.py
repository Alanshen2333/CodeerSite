from typing import Optional, List
from app.extensions import db
from app.models.kanban_column import KanbanColumn
from app.models.kanban_card import KanbanCard


class KanbanService:
    # -- Columns --
    @staticmethod
    def create_column(project_id: str, title: str) -> KanbanColumn:
        # Auto-position at the end
        max_pos = (
            db.session.query(db.func.max(KanbanColumn.position))
            .filter_by(project_id=project_id)
            .scalar()
        )
        col = KanbanColumn(
            project_id=project_id,
            title=title,
            position=(max_pos + 1) if max_pos is not None else 0,
        )
        db.session.add(col)
        db.session.commit()
        return col

    @staticmethod
    def update_column(column: KanbanColumn, title: str = None) -> KanbanColumn:
        if title is not None:
            column.title = title
        db.session.commit()
        return column

    @staticmethod
    def delete_column(column: KanbanColumn):
        db.session.delete(column)
        db.session.commit()

    @staticmethod
    def get_column(column_id: str) -> Optional[KanbanColumn]:
        return db.session.get(KanbanColumn, column_id)

    @staticmethod
    def get_columns(project_id: str) -> List[KanbanColumn]:
        return (
            KanbanColumn.query.filter_by(project_id=project_id)
            .order_by(KanbanColumn.position.asc())
            .all()
        )

    @staticmethod
    def reorder_columns(project_id: str, column_ids: List[str]):
        """Update column positions based on ordered list of IDs.

        校验传入的 column_ids 与项目实际列完全一致（数量、元素），
        不允许缺失、重复或混入其他项目的列 ID。
        """
        existing = KanbanService.get_columns(project_id)
        existing_ids = {c.id for c in existing}

        if len(column_ids) != len(existing_ids):
            raise ValueError("column_ids 数量与项目实际列数不一致。")
        if len(set(column_ids)) != len(column_ids):
            raise ValueError("column_ids 包含重复 ID。")
        provided = set(column_ids)
        if provided != existing_ids:
            raise ValueError("column_ids 包含不属于本项目的列 ID 或缺少部分列。")

        for pos, col_id in enumerate(column_ids):
            col = db.session.get(KanbanColumn, col_id)
            if col:
                col.position = pos
        db.session.commit()

    # -- Cards --
    @staticmethod
    def create_card(column_id: str, title: str, issue_id: str = None) -> KanbanCard:
        max_pos = (
            db.session.query(db.func.max(KanbanCard.position))
            .filter_by(column_id=column_id)
            .scalar()
        )
        card = KanbanCard(
            column_id=column_id,
            title=title,
            issue_id=issue_id,
            position=(max_pos + 1) if max_pos is not None else 0,
        )
        db.session.add(card)
        db.session.commit()
        return card

    @staticmethod
    def update_card(card: KanbanCard, title: str = None) -> KanbanCard:
        if title is not None:
            card.title = title
        db.session.commit()
        return card

    @staticmethod
    def delete_card(card: KanbanCard):
        db.session.delete(card)
        db.session.commit()

    @staticmethod
    def move_card(card: KanbanCard, target_column_id: str, target_position: int):
        """Move a card to a different column and/or position.

        target_position 会 clamp 到 [0, 目标列卡片数]（跨列）或
        [0, 当前列卡片数 - 1]（同列），防止负数位置或空洞。
        """
        target_count = KanbanCard.query.filter_by(column_id=target_column_id).count()
        if card.column_id == target_column_id:
            max_pos = max(target_count - 1, 0)
        else:
            max_pos = target_count
        target_position = max(0, min(target_position, max_pos))
        old_column_id = card.column_id

        # Shift cards in target column to make room
        if card.column_id != target_column_id:
            # Remove from old column, decrement higher positions
            KanbanCard.query.filter(
                KanbanCard.column_id == card.column_id,
                KanbanCard.position > card.position,
            ).update({KanbanCard.position: KanbanCard.position - 1})

            # Increment positions >= target in new column
            KanbanCard.query.filter(
                KanbanCard.column_id == target_column_id,
                KanbanCard.position >= target_position,
            ).update({KanbanCard.position: KanbanCard.position + 1})

            card.column_id = target_column_id
            card.position = target_position
        else:
            # Same column, reorder
            old_pos = card.position
            if old_pos < target_position:
                KanbanCard.query.filter(
                    KanbanCard.column_id == card.column_id,
                    KanbanCard.position > old_pos,
                    KanbanCard.position <= target_position,
                ).update({KanbanCard.position: KanbanCard.position - 1})
            elif old_pos > target_position:
                KanbanCard.query.filter(
                    KanbanCard.column_id == card.column_id,
                    KanbanCard.position >= target_position,
                    KanbanCard.position < old_pos,
                ).update({KanbanCard.position: KanbanCard.position + 1})
            card.position = target_position

        # Normalize positions to remove any gaps
        KanbanService._normalize_positions(target_column_id)
        if old_column_id != target_column_id:
            KanbanService._normalize_positions(old_column_id)

        db.session.commit()
        return card

    @staticmethod
    def _normalize_positions(column_id: str):
        """Renumber all cards in a column to be contiguous 0, 1, 2, ..."""
        cards = (
            KanbanCard.query.filter_by(column_id=column_id)
            .order_by(KanbanCard.position.asc())
            .all()
        )
        for i, card in enumerate(cards):
            card.position = i

    @staticmethod
    def get_card(card_id: str) -> Optional[KanbanCard]:
        return db.session.get(KanbanCard, card_id)

    @staticmethod
    def get_cards(column_id: str) -> List[KanbanCard]:
        return (
            KanbanCard.query.filter_by(column_id=column_id)
            .order_by(KanbanCard.position.asc())
            .all()
        )
