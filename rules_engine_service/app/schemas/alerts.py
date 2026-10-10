from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel

class WhatsNewCard(BaseModel):
    alert_id: int
    document_id: Optional[int] = None
    regulator: str
    document_title: str
    version: str
    effective_date: Optional[date] = None
    diff_summary: str
    impact_level: str
    is_read: bool
    created_at: datetime

class AlertListResponse(BaseModel):
    total: int
    unread_count: int
    alerts: List[WhatsNewCard]