"""Service layer for project onboarding checklists."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.onboarding_checklist import (
    ChecklistItemType,
    OnboardingAssignment,
    OnboardingChecklist,
    OnboardingItem,
    OnboardingItemCompletion,
)
from app.schemas.onboarding_checklist import (
    AssignmentCreate,
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentWithProgress,
    ChecklistCreate,
    ChecklistListResponse,
    ChecklistResponse,
    ChecklistStats,
    ChecklistWithItems,
    ChecklistUpdate,
    ItemCompletionCreate,
    ItemCompletionResponse,
    OnboardingItemCreate,
    OnboardingItemResponse,
    OnboardingItemUpdate,
    ProjectOnboardingStats,
)


class OnboardingChecklistService:
    """Business logic for onboarding checklists."""

    # ── Checklist CRUD ───────────────────────────────────────────────

    @staticmethod
    def create_checklist(
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ChecklistCreate,
    ) -> ChecklistResponse:
        checklist = OnboardingChecklist(
            project_id=project_id,
            created_by_id=user_id,
            title=data.title,
            description=data.description,
            is_default=data.is_default,
        )
        db.add(checklist)
        db.commit()
        db.refresh(checklist)
        return ChecklistResponse.model_validate(checklist)

    @staticmethod
    def list_checklists(
        db: Session,
        project_id: uuid.UUID,
        include_archived: bool = False,
    ) -> ChecklistListResponse:
        query = db.query(OnboardingChecklist).filter(
            OnboardingChecklist.project_id == project_id
        )
        if not include_archived:
            query = query.filter(OnboardingChecklist.is_archived == False)

        total = query.count()
        items = query.order_by(OnboardingChecklist.created_at.desc()).all()
        return ChecklistListResponse(
            items=[ChecklistResponse.model_validate(i) for i in items],
            total=total,
        )

    @staticmethod
    def get_checklist(
        db: Session,
        checklist_id: uuid.UUID,
    ) -> Optional[ChecklistWithItems]:
        checklist = (
            db.query(OnboardingChecklist)
            .options(joinedload(OnboardingChecklist.items))
            .filter(OnboardingChecklist.id == checklist_id)
            .first()
        )
        if not checklist:
            return None

        items = sorted(checklist.items, key=lambda x: x.order)
        result = ChecklistWithItems(
            **ChecklistResponse.model_validate(checklist).model_dump(),
            items=[OnboardingItemResponse.model_validate(i) for i in items],
            item_count=len(items),
            required_count=sum(1 for i in items if i.is_required),
        )
        return result

    @staticmethod
    def update_checklist(
        db: Session,
        checklist_id: uuid.UUID,
        data: ChecklistUpdate,
    ) -> Optional[ChecklistResponse]:
        checklist = db.query(OnboardingChecklist).filter(
            OnboardingChecklist.id == checklist_id
        ).first()
        if not checklist:
            return None

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(checklist, key, value)

        db.commit()
        db.refresh(checklist)
        return ChecklistResponse.model_validate(checklist)

    @staticmethod
    def delete_checklist(db: Session, checklist_id: uuid.UUID) -> bool:
        checklist = db.query(OnboardingChecklist).filter(
            OnboardingChecklist.id == checklist_id
        ).first()
        if not checklist:
            return False
        db.delete(checklist)
        db.commit()
        return True

    # ── Items ────────────────────────────────────────────────────────

    @staticmethod
    def add_item(
        db: Session,
        checklist_id: uuid.UUID,
        data: OnboardingItemCreate,
    ) -> Optional[OnboardingItemResponse]:
        checklist = db.query(OnboardingChecklist).filter(
            OnboardingChecklist.id == checklist_id
        ).first()
        if not checklist:
            return None

        item = OnboardingItem(
            checklist_id=checklist_id,
            title=data.title,
            description=data.description,
            item_type=data.item_type,
            order=data.order,
            is_required=data.is_required,
            resource_url=data.resource_url,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return OnboardingItemResponse.model_validate(item)

    @staticmethod
    def update_item(
        db: Session,
        item_id: uuid.UUID,
        data: OnboardingItemUpdate,
    ) -> Optional[OnboardingItemResponse]:
        item = db.query(OnboardingItem).filter(
            OnboardingItem.id == item_id
        ).first()
        if not item:
            return None

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)

        db.commit()
        db.refresh(item)
        return OnboardingItemResponse.model_validate(item)

    @staticmethod
    def delete_item(db: Session, item_id: uuid.UUID) -> bool:
        item = db.query(OnboardingItem).filter(
            OnboardingItem.id == item_id
        ).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

    # ── Assignments ──────────────────────────────────────────────────

    @staticmethod
    def assign_checklist(
        db: Session,
        checklist_id: uuid.UUID,
        user_id: uuid.UUID,
        data: AssignmentCreate,
    ) -> Optional[AssignmentResponse]:
        checklist = db.query(OnboardingChecklist).filter(
            OnboardingChecklist.id == checklist_id
        ).first()
        if not checklist:
            return None

        existing = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.checklist_id == checklist_id,
            OnboardingAssignment.user_id == data.user_id,
        ).first()
        if existing:
            return AssignmentResponse.model_validate(existing)

        assignment = OnboardingAssignment(
            checklist_id=checklist_id,
            user_id=data.user_id,
            assigned_by_id=user_id,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return AssignmentResponse.model_validate(assignment)

    @staticmethod
    def batch_assign(
        db: Session,
        checklist_id: uuid.UUID,
        assigned_by_id: uuid.UUID,
        user_ids: List[uuid.UUID],
    ) -> List[AssignmentResponse]:
        checklist = db.query(OnboardingChecklist).filter(
            OnboardingChecklist.id == checklist_id
        ).first()
        if not checklist:
            return []

        results = []
        for uid in user_ids:
            existing = db.query(OnboardingAssignment).filter(
                OnboardingAssignment.checklist_id == checklist_id,
                OnboardingAssignment.user_id == uid,
            ).first()
            if existing:
                results.append(AssignmentResponse.model_validate(existing))
                continue

            assignment = OnboardingAssignment(
                checklist_id=checklist_id,
                user_id=uid,
                assigned_by_id=assigned_by_id,
            )
            db.add(assignment)
            db.flush()
            db.refresh(assignment)
            results.append(AssignmentResponse.model_validate(assignment))

        db.commit()
        return results

    @staticmethod
    def list_assignments(
        db: Session,
        checklist_id: uuid.UUID,
        completed_only: Optional[bool] = None,
    ) -> AssignmentListResponse:
        query = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.checklist_id == checklist_id
        )
        if completed_only is not None:
            query = query.filter(OnboardingAssignment.is_completed == completed_only)

        total = query.count()
        items = query.order_by(OnboardingAssignment.created_at.desc()).all()
        return AssignmentListResponse(
            items=[AssignmentResponse.model_validate(i) for i in items],
            total=total,
        )

    @staticmethod
    def get_assignment_progress(
        db: Session,
        assignment_id: uuid.UUID,
    ) -> Optional[AssignmentWithProgress]:
        assignment = (
            db.query(OnboardingAssignment)
            .options(joinedload(OnboardingAssignment.item_completions))
            .filter(OnboardingAssignment.id == assignment_id)
            .first()
        )
        if not assignment:
            return None

        checklist = db.query(OnboardingChecklist).options(
            joinedload(OnboardingChecklist.items)
        ).filter(OnboardingChecklist.id == assignment.checklist_id).first()

        total_items = len(checklist.items) if checklist else 0
        completed_item_ids = {c.item_id for c in assignment.item_completions}
        completed = len(completed_item_ids)

        required_items = [i for i in (checklist.items if checklist else []) if i.is_required]
        required_remaining = sum(
            1 for i in required_items if i.id not in completed_item_ids
        )

        progress = (completed / total_items * 100) if total_items > 0 else 0.0

        return AssignmentWithProgress(
            **AssignmentResponse.model_validate(assignment).model_dump(),
            total_items=total_items,
            completed_items=completed,
            progress_percent=round(progress, 1),
            required_remaining=required_remaining,
        )

    @staticmethod
    def complete_item(
        db: Session,
        assignment_id: uuid.UUID,
        item_id: uuid.UUID,
        user_id: uuid.UUID,
        data: Optional[ItemCompletionCreate] = None,
    ) -> Optional[ItemCompletionResponse]:
        assignment = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.id == assignment_id
        ).first()
        if not assignment or assignment.user_id != user_id:
            return None

        existing = db.query(OnboardingItemCompletion).filter(
            OnboardingItemCompletion.assignment_id == assignment_id,
            OnboardingItemCompletion.item_id == item_id,
        ).first()
        if existing:
            return ItemCompletionResponse.model_validate(existing)

        if not assignment.started_at:
            assignment.started_at = datetime.now(timezone.utc)

        completion = OnboardingItemCompletion(
            assignment_id=assignment_id,
            item_id=item_id,
            notes=data.notes if data else None,
        )
        db.add(completion)

        checklist = db.query(OnboardingChecklist).options(
            joinedload(OnboardingChecklist.items)
        ).filter(OnboardingChecklist.id == assignment.checklist_id).first()

        if checklist:
            all_item_ids = {i.id for i in checklist.items}
            completed_ids = {item_id}
            existing_completions = (
                db.query(OnboardingItemCompletion.item_id)
                .filter(OnboardingItemCompletion.assignment_id == assignment_id)
                .all()
            )
            completed_ids.update(c[0] for c in existing_completions)
            completed_ids.add(item_id)

            required_ids = {i.id for i in checklist.items if i.is_required}
            if required_ids and required_ids.issubset(completed_ids):
                assignment.is_completed = True
                assignment.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(completion)
        return ItemCompletionResponse.model_validate(completion)

    # ── Statistics ───────────────────────────────────────────────────

    @staticmethod
    def get_checklist_stats(
        db: Session,
        checklist_id: uuid.UUID,
    ) -> Optional[ChecklistStats]:
        checklist = db.query(OnboardingChecklist).filter(
            OnboardingChecklist.id == checklist_id
        ).first()
        if not checklist:
            return None

        total_assigned = (
            db.query(func.count(OnboardingAssignment.id))
            .filter(OnboardingAssignment.checklist_id == checklist_id)
            .scalar()
        )
        completed_count = (
            db.query(func.count(OnboardingAssignment.id))
            .filter(
                OnboardingAssignment.checklist_id == checklist_id,
                OnboardingAssignment.is_completed == True,
            )
            .scalar()
        )

        in_progress = (
            db.query(func.count(OnboardingAssignment.id))
            .filter(
                OnboardingAssignment.checklist_id == checklist_id,
                OnboardingAssignment.is_completed == False,
                OnboardingAssignment.started_at.isnot(None),
            )
            .scalar()
        )

        not_started = total_assigned - completed_count - in_progress

        assignments = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.checklist_id == checklist_id
        ).all()

        total_items = (
            db.query(func.count(OnboardingItem.id))
            .filter(OnboardingItem.checklist_id == checklist_id)
            .scalar()
        )

        avg_progress = 0.0
        if assignments and total_items > 0:
            progress_list = []
            for a in assignments:
                completed = (
                    db.query(func.count(OnboardingItemCompletion.id))
                    .filter(OnboardingItemCompletion.assignment_id == a.id)
                    .scalar()
                )
                progress_list.append(completed / total_items * 100)
            avg_progress = round(sum(progress_list) / len(progress_list), 1)

        return ChecklistStats(
            checklist_id=checklist_id,
            total_assigned=total_assigned or 0,
            completed_count=completed_count or 0,
            in_progress_count=in_progress or 0,
            not_started_count=not_started or 0,
            average_completion_percent=avg_progress,
        )

    @staticmethod
    def get_project_onboarding_stats(
        db: Session,
        project_id: uuid.UUID,
    ) -> ProjectOnboardingStats:
        total_checklists = (
            db.query(func.count(OnboardingChecklist.id))
            .filter(OnboardingChecklist.project_id == project_id)
            .scalar()
        )
        checklist_ids = [
            c[0]
            for c in db.query(OnboardingChecklist.id)
            .filter(OnboardingChecklist.project_id == project_id)
            .all()
        ]

        total_assignments = 0
        completed_assignments = 0
        if checklist_ids:
            total_assignments = (
                db.query(func.count(OnboardingAssignment.id))
                .filter(OnboardingAssignment.checklist_id.in_(checklist_ids))
                .scalar()
            )
            completed_assignments = (
                db.query(func.count(OnboardingAssignment.id))
                .filter(
                    OnboardingAssignment.checklist_id.in_(checklist_ids),
                    OnboardingAssignment.is_completed == True,
                )
                .scalar()
            )

        avg_progress = (
            round(completed_assignments / total_assignments * 100, 1)
            if total_assignments > 0
            else 0.0
        )

        most_popular = None
        if checklist_ids:
            result = (
                db.query(
                    OnboardingChecklist.title,
                    func.count(OnboardingAssignment.id).label("cnt"),
                )
                .join(
                    OnboardingAssignment,
                    OnboardingAssignment.checklist_id == OnboardingChecklist.id,
                )
                .filter(OnboardingChecklist.project_id == project_id)
                .group_by(OnboardingChecklist.title)
                .order_by(func.count(OnboardingAssignment.id).desc())
                .first()
            )
            if result:
                most_popular = result[0]

        return ProjectOnboardingStats(
            project_id=project_id,
            total_checklists=total_checklists or 0,
            total_assignments=total_assignments or 0,
            completed_assignments=completed_assignments or 0,
            average_progress=avg_progress,
            most_popular_checklist=most_popular,
        )
