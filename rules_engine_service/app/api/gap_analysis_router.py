from fastapi import APIRouter, Depends, Query
from app.core.security import verify_bearer_token
from app.schemas.gap_analysis import ComplianceChecklistResponse, GapAnalysisReport
from app.services.gap_analysis_service import gap_analysis_service
router = APIRouter(tags=['Gap Analysis & Compliance Checklist'])

@router.get('/gap-analysis', response_model=GapAnalysisReport, summary='Perform schema-to-regulation gap analysis')
def get_gap_analysis(regulator: str=Query(default='EMIR', description='Target regulatory regime: EMIR, MiFID II, or Dodd-Frank'), _auth: bool=Depends(verify_bearer_token)) -> GapAnalysisReport:
    return gap_analysis_service.perform_gap_analysis(regulator=regulator)

@router.get('/checklist', response_model=ComplianceChecklistResponse, summary='Retrieve regulatory compliance checklist')
def get_compliance_checklist(framework: str=Query(default='MiFID II', description='Regulatory framework: MiFID II, EMIR, Dodd-Frank'), _auth: bool=Depends(verify_bearer_token)) -> ComplianceChecklistResponse:
    return gap_analysis_service.get_compliance_checklist(framework=framework)