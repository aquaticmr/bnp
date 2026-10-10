import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import DocumentMetadataRecord

logger = logging.getLogger(__name__)


class VersioningService:
    def get_documents_by_regulator(self, db: Session, regulator: str) -> List[DocumentMetadataRecord]:
        return (
            db.query(DocumentMetadataRecord)
            .filter(DocumentMetadataRecord.regulator.ilike(regulator))
            .order_by(DocumentMetadataRecord.document_id.asc())
            .all()
        )

    def get_all_documents(self, db: Session) -> List[DocumentMetadataRecord]:
        return (
            db.query(DocumentMetadataRecord)
            .order_by(DocumentMetadataRecord.document_id.desc())
            .all()
        )

    def get_document_by_id(self, db: Session, doc_id: int) -> Optional[DocumentMetadataRecord]:
        return (
            db.query(DocumentMetadataRecord)
            .filter(DocumentMetadataRecord.document_id == doc_id)
            .first()
        )

    def record_document_version(
        self,
        db: Session,
        file_name: str,
        regulator: str,
        version: str,
        jurisdiction: Optional[str] = None,
        category: Optional[str] = None,
        effective_date=None,
        storage_path: Optional[str] = None,
        parent_doc_id: Optional[int] = None,
    ) -> DocumentMetadataRecord:
        record = DocumentMetadataRecord(
            file_name=file_name,
            regulator=regulator,
            version=version,
            jurisdiction=jurisdiction,
            category=category,
            effective_date=effective_date,
            storage_path=storage_path,
            parent_doc_id=parent_doc_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record


versioning_service = VersioningService()
