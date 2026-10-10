from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.security import verify_bearer_token
from app.db.models import DocumentMetadataRecord
from app.db.session import get_db
from app.schemas.alerts import AlertListResponse, WhatsNewCard
from app.services.diff_service import diff_alert_service
router = APIRouter(prefix='/alerts', tags=["Alerts & What's New Domain"])

@router.get('', response_model=AlertListResponse, summary='Retrieve Alert Panel notifications')
def get_alerts(limit: int=Query(default=20, ge=1, le=100), db: Session=Depends(get_db), _auth: bool=Depends(verify_bearer_token)) -> AlertListResponse:
    return diff_alert_service.get_alerts(db, limit=limit)

@router.put('/{alert_id}/read', summary='Mark an alert notification as acknowledged/read')
def mark_read(alert_id: int, db: Session=Depends(get_db), _auth: bool=Depends(verify_bearer_token)):
    success = diff_alert_service.mark_alert_read(db, alert_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Alert notification {alert_id} not found')
    return {'success': True, 'alert_id': alert_id}

@router.post('/whats-new', response_model=WhatsNewCard, summary="Generate a What's New diff card for a document")
def generate_card(document_id: Optional[int]=Query(default=None), regulator: str=Query(..., description='Regulator name, e.g. EMIR, MiFID II'), version: str=Query(..., description='Document version'), diff_summary: Optional[str]=Query(default=None, description='Custom diff explanation'), db: Session=Depends(get_db), _auth: bool=Depends(verify_bearer_token)) -> WhatsNewCard:
    doc = DocumentMetadataRecord(document_id=document_id, file_name=f'{regulator}_{version}_Handbook.pdf', regulator=regulator, version=version)
    return diff_alert_service.generate_whats_new_card(db, new_doc=doc, custom_diff=diff_summary)