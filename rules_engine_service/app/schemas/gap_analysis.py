from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class GapStatus(str, Enum):
    MAPPED = 'MAPPED'
    MISSING = 'MISSING'
    PARTIAL = 'PARTIAL'

class FieldComplianceGap(BaseModel):
    mandate_regulator: str
    mandate_article: str
    required_field: str
    mapped_schema_field: Optional[str] = None
    status: GapStatus
    risk_level: str
    remediation_action: str

class GapAnalysisReport(BaseModel):
    regulator: str
    total_mandated_fields: int
    mapped_fields_count: int
    missing_fields_count: int
    compliance_score_percentage: float
    gaps: List[FieldComplianceGap]

class ChecklistStatus(str, Enum):
    SATISFIED = 'SATISFIED'
    ACTION_REQUIRED = 'ACTION_REQUIRED'
    NOT_APPLICABLE = 'NOT_APPLICABLE'

class ComplianceChecklistItem(BaseModel):
    item_id: str
    framework: str
    requirement: str
    verification_criteria: str
    status: ChecklistStatus
    owner_team: str

class ComplianceChecklistResponse(BaseModel):
    framework: str
    total_checks: int
    satisfied_count: int
    action_required_count: int
    checklist: List[ComplianceChecklistItem]