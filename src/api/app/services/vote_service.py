from typing import Optional
from app.extensions import db
from app.models.vote import Vote
from app.models.question import Question
from app.models.answer import Answer
from app.models.user import User
from app.services.notification_service import NotificationService

REPUTATION_UPVOTE_GAIN = 10
REPUTATION_DOWNVOTE_LOSS = -2
REPUTATION_ACCEPT_GAIN = 15


class VoteService:
    @staticmethod
    def vote(user_id: str, vote_type: str, target_type: str, target_id: str) -> Vote:
        """Cast a vote (up/down). If user already voted, update the vote_type.
        Updates vote_count on the target and adjusts author reputation.
        """
        if vote_type not in ("up", "down"):
            raise ValueError("vote_type must be 'up' or 'down'.")

        # Check target exists
        target = VoteService._get_target(target_type, target_id)
        if not target:
            raise ValueError(f"{target_type} not found.")

        # Cannot vote on own content
        if target.author_id == user_id:
            raise ValueError("You cannot vote on your own content.")

        # Find existing vote or create new
        existing = Vote.query.filter_by(
            user_id=user_id, target_type=target_type, target_id=target_id
        ).first()

        old_vote_type = None
        if existing:
            if existing.vote_type == vote_type:
                # Same vote -> remove it (toggle off)
                VoteService._remove_vote(existing, target)
                return existing
            old_vote_type = existing.vote_type
            existing.vote_type = vote_type
            vote = existing
        else:
            vote = Vote(
                user_id=user_id,
                vote_type=vote_type,
                target_type=target_type,
                target_id=target_id,
            )
            db.session.add(vote)

        db.session.flush()

        # Update target vote_count
        VoteService._update_vote_count(target, vote_type, old_vote_type)

        # Update reputations
        VoteService._update_reputation_for_vote(target, vote_type, old_vote_type)

        db.session.commit()

        # Notify target author (only for new votes, not toggling/changing)
        if old_vote_type is None and target.author_id != user_id:
            target_type_label = "问题" if target_type == "question" else "回答"
            vote_label = "赞" if vote_type == "up" else "踩"
            target_title = getattr(target, "title", "") or getattr(target, "body", "")[:100]
            NotificationService.create(
                recipient_id=target.author_id,
                type_="new_vote",
                title=f"你的{target_type_label}收到了一个{vote_label}",
                body=target_title[:200],
                link=f"/questions/{target.question_id if hasattr(target, 'question_id') else target.id}",
                source_type=target_type,
                source_id=target_id,
            )

        return vote

    @staticmethod
    def remove_vote(user_id: str, target_type: str, target_id: str):
        """Remove a vote entirely."""
        existing = Vote.query.filter_by(
            user_id=user_id, target_type=target_type, target_id=target_id
        ).first()
        if not existing:
            raise ValueError("Vote not found.")

        target = VoteService._get_target(target_type, target_id)
        if target:
            VoteService._remove_vote(existing, target)
        else:
            db.session.delete(existing)
            db.session.commit()

    @staticmethod
    def _remove_vote(vote: Vote, target):
        """Internal: remove a vote and adjust counts."""
        # Undo reputation change
        VoteService._update_reputation_for_vote(target, vote.vote_type, None, undo=True)

        # Update vote_count
        if vote.vote_type == "up":
            target.vote_count = max(0, target.vote_count - 1)
        else:
            target.vote_count += 1

        db.session.delete(vote)
        db.session.commit()

    @staticmethod
    def _update_vote_count(target, new_vote_type: str, old_vote_type: Optional[str]):
        """Update target.vote_count based on vote change."""
        if old_vote_type is None:
            # New vote
            if new_vote_type == "up":
                target.vote_count += 1
            else:
                target.vote_count = max(0, target.vote_count - 1)
        else:
            # Changing vote
            if old_vote_type == "up" and new_vote_type == "down":
                target.vote_count = max(0, target.vote_count - 2)
            elif old_vote_type == "down" and new_vote_type == "up":
                target.vote_count += 2

    @staticmethod
    def _update_reputation_for_vote(target, vote_type: str, old_vote_type: Optional[str], undo: bool = False):
        """Update the target author's reputation."""
        author = db.session.get(User, target.author_id)
        if not author:
            return

        multiplier = -1 if undo else 1

        if old_vote_type is None:
            # New vote
            if vote_type == "up":
                author.reputation += REPUTATION_UPVOTE_GAIN * multiplier
            else:
                author.reputation += REPUTATION_DOWNVOTE_LOSS * multiplier
        else:
            # Changing vote: reverse old, apply new
            if old_vote_type == "up" and vote_type == "down":
                author.reputation += (REPUTATION_DOWNVOTE_LOSS - REPUTATION_UPVOTE_GAIN) * multiplier
            elif old_vote_type == "down" and vote_type == "up":
                author.reputation += (REPUTATION_UPVOTE_GAIN - REPUTATION_DOWNVOTE_LOSS) * multiplier

    @staticmethod
    def _get_target(target_type: str, target_id: str):
        if target_type == "question":
            return db.session.get(Question, target_id)
        elif target_type == "answer":
            return db.session.get(Answer, target_id)
        return None

    @staticmethod
    def get_user_vote(user_id: str, target_type: str, target_id: str) -> Optional[Vote]:
        return Vote.query.filter_by(
            user_id=user_id, target_type=target_type, target_id=target_id
        ).first()

    @staticmethod
    def get_user_votes_for_targets(user_id: str, target_type: str, target_ids: list) -> dict:
        """Get user's votes for a list of targets. Returns {target_id: vote_type}."""
        votes = Vote.query.filter(
            Vote.user_id == user_id,
            Vote.target_type == target_type,
            Vote.target_id.in_(target_ids),
        ).all()
        return {v.target_id: v.vote_type for v in votes}
