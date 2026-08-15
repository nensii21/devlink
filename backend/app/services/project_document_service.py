from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_document import ProjectDocument
from app.models.project import Project


class ProjectDocumentService:
    @staticmethod
    def create_document(
        db: Session,
        project_id: UUID,
        user_id: UUID,
        title: str = "Untitled Document",
        content: str = "",
    ) -> ProjectDocument:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )

        doc = ProjectDocument(
            project_id=project_id,
            title=title,
            content=content,
            version=1,
            created_by_id=user_id,
            last_edited_by_id=user_id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_document(db: Session, doc_id: UUID) -> ProjectDocument:
        doc = db.get(ProjectDocument, doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace document not found.",
            )
        return doc

    @staticmethod
    def list_project_documents(db: Session, project_id: UUID) -> list[ProjectDocument]:
        return (
            db.query(ProjectDocument)
            .filter(ProjectDocument.project_id == project_id)
            .order_by(ProjectDocument.updated_at.desc())
            .all()
        )

    @staticmethod
    def update_document(
        db: Session,
        doc_id: UUID,
        user_id: UUID,
        title: str | None = None,
        content: str | None = None,
        base_version: int | None = None,
    ) -> tuple[ProjectDocument, bool]:
        """
        Updates document content and handles conflict detection via base_version.

        Returns (updated_doc, is_conflict) tuple.
        """
        doc = db.get(ProjectDocument, doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace document not found.",
            )

        is_conflict = False

        # Version conflict detection
        if base_version is not None and base_version < doc.version:
            is_conflict = True
            # Conflict resolution: if content is provided, append/merge or return current server state
            if content is not None and content != doc.content:
                # Merge logic: append new additions if distinct or retain server latest
                if doc.content and content and not doc.content.endswith(content):
                    merged_content = f"{doc.content}\n\n--- [Collaborator Edit Conflict Resolved] ---\n{content}"
                    doc.content = merged_content
            doc.version += 1
            doc.last_edited_by_id = user_id
            db.commit()
            db.refresh(doc)
            return doc, is_conflict

        if title is not None:
            doc.title = title

        if content is not None:
            doc.content = content

        doc.version += 1
        doc.last_edited_by_id = user_id

        db.commit()
        db.refresh(doc)
        return doc, is_conflict

    @staticmethod
    def delete_document(db: Session, doc_id: UUID) -> None:
        doc = db.get(ProjectDocument, doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace document not found.",
            )
        db.delete(doc)
        db.commit()
