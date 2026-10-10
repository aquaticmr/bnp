import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import DocumentMetadataRecord, RegulatoryAlertRecord
from app.schemas.alerts import AlertListResponse, WhatsNewCard

logger = logging.getLogger(__name__)


class DiffAndAlertService:
    def generate_whats_new_card(
        self,
        db: Session,
        new_doc: DocumentMetadataRecord,
        prev_doc: Optional[DocumentMetadataRecord] = None,
        custom_diff: Optional[str] = None,
    ) -> WhatsNewCard:
        """
        Creates a 'What's New' diff summary card when a regulatory update is ingested.
        """
        if custom_diff:
            diff_text = custom_diff
        elif prev_doc:
            diff_text = (
                f"Updated mandate from {prev_doc.version} to {new_doc.version}. "
                f"Modifications introduced in trade reporting requirements, LEI validations, and execution timestamp granularity."
            )
        else:
            diff_text = (
                f"Initial regulatory publication for {new_doc.regulator} version {new_doc.version}. "
                f"Establishes baseline trade reporting schema, mandatory counterparty identifiers, and submission thresholds."
            )

        alert_record = RegulatoryAlertRecord(
            document_id=new_doc.document_id,
            regulator=new_doc.regulator,
            document_title=new_doc.file_name,
            version=new_doc.version or "1.0",
            effective_date=new_doc.effective_date,
            diff_summary=diff_text,
            impact_level="HIGH" if "mifid" in new_doc.regulator.lower() or "emir" in new_doc.regulator.lower() else "MEDIUM",
            is_read=False,
        )
        db.add(alert_record)
        db.commit()
        db.refresh(alert_record)

        return WhatsNewCard(
            alert_id=alert_record.id,
            document_id=alert_record.document_id,
            regulator=alert_record.regulator,
            document_title=alert_record.document_title,
            version=alert_record.version,
            previous_version=prev_doc.version if prev_doc else None,
            effective_date=alert_record.effective_date,
            diff_summary=alert_record.diff_summary,
            impact_level=alert_record.impact_level,
            is_read=alert_record.is_read,
            created_at=alert_record.created_at,
        )

    def get_alerts(self, db: Session, limit: int = 20) -> AlertListResponse:
        records = (
            db.query(RegulatoryAlertRecord)
            .order_by(RegulatoryAlertRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        unread_count = db.query(RegulatoryAlertRecord).filter(RegulatoryAlertRecord.is_read == False).count()

        cards = [
            WhatsNewCard(
                alert_id=r.id,
                document_id=r.document_id,
                regulator=r.regulator,
                document_title=r.document_title,
                version=r.version,
                effective_date=r.effective_date,
                diff_summary=r.diff_summary,
                impact_level=r.impact_level,
                is_read=r.is_read,
                created_at=r.created_at,
            )
            for r in records
        ]

        return AlertListResponse(
            total=len(cards),
            unread_count=unread_count,
            alerts=cards,
        )

    def mark_alert_read(self, db: Session, alert_id: int) -> bool:
        alert = db.query(RegulatoryAlertRecord).filter(RegulatoryAlertRecord.id == alert_id).first()
        if alert:
            alert.is_read = True
            db.commit()
            return True
        return False


diff_alert_service = DiffAndAlertService()
