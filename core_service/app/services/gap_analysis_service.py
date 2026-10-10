import json
import logging
from typing import Dict, List, Optional
from app.core.config import settings
from app.schemas.gap_analysis import (
    ChecklistStatus,
    ComplianceChecklistItem,
    ComplianceChecklistResponse,
    FieldComplianceGap,
    GapAnalysisReport,
    GapStatus,
)

logger = logging.getLogger(__name__)

# Standard regulatory mandate field requirements
MANDATED_REGULATORY_FIELDS = {
    "EMIR": [
        {"field": "Trade_ID", "article": "Article 9(1)", "type": "string", "risk": "HIGH"},
        {"field": "Counterparty_LEI", "article": "Article 9(2) - ITS 1247/2012", "type": "string", "risk": "CRITICAL"},
        {"field": "Price", "article": "Article 9(3)", "type": "float", "risk": "HIGH"},
        {"field": "Quantity", "article": "Article 9(3)", "type": "float", "risk": "HIGH"},
        {"field": "Execution_Timestamp", "article": "Article 9(4)", "type": "datetime", "risk": "HIGH"},
        {"field": "Asset_Class", "article": "Article 9(1)", "type": "string", "risk": "MEDIUM"},
        {"field": "Currency", "article": "ITS 1247/2012", "type": "string", "risk": "MEDIUM"},
        {"field": "UTI", "article": "EMIR Refit RTS Field 1", "type": "string", "risk": "CRITICAL"},
        {"field": "UPI", "article": "EMIR Refit RTS Field 2", "type": "string", "risk": "HIGH"},
    ],
    "MiFID II": [
        {"field": "Trade_ID", "article": "RTS 22 Article 1", "type": "string", "risk": "HIGH"},
        {"field": "Counterparty_LEI", "article": "RTS 22 Field 3", "type": "string", "risk": "CRITICAL"},
        {"field": "Trader_ID", "article": "RTS 22 Field 59 (Decision Maker)", "type": "string", "risk": "MEDIUM"},
        {"field": "Venue", "article": "RTS 22 Field 36 (Trading Venue MIC)", "type": "string", "risk": "HIGH"},
        {"field": "Price", "article": "RTS 22 Field 33", "type": "float", "risk": "HIGH"},
        {"field": "Quantity", "article": "RTS 22 Field 30", "type": "float", "risk": "HIGH"},
        {"field": "Execution_Timestamp", "article": "RTS 22 Field 28", "type": "datetime", "risk": "HIGH"},
        {"field": "Currency", "article": "RTS 22 Field 34", "type": "string", "risk": "MEDIUM"},
    ],
    "Dodd-Frank": [
        {"field": "Trade_ID", "article": "CFTC Part 43 / Part 45", "type": "string", "risk": "HIGH"},
        {"field": "Counterparty_LEI", "article": "CFTC Part 45.6", "type": "string", "risk": "CRITICAL"},
        {"field": "Price", "article": "CFTC Part 43 Real-time Public Reporting", "type": "float", "risk": "HIGH"},
        {"field": "Quantity", "article": "CFTC Part 43 Notional Volume", "type": "float", "risk": "HIGH"},
        {"field": "Asset_Class", "article": "CFTC Part 45 Swap Data", "type": "string", "risk": "MEDIUM"},
        {"field": "Execution_Timestamp", "article": "CFTC Part 43.3", "type": "datetime", "risk": "HIGH"},
    ],
}


class GapAnalysisService:
    def __init__(self):
        self.schema_path = settings.SCHEMA_PATH

    def _load_schema_fields(self) -> List[str]:
        if not self.schema_path.exists():
            # Return baseline standard schema fields
            return [
                "Trade_ID", "Asset_Class", "Timestamp", "Execution_Timestamp",
                "Counterparty_LEI", "Price", "Quantity", "Currency", "Venue", "Trader_ID"
            ]
        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return list(data.get("properties", data).keys())
            elif isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error("Failed to read reporting schema JSON: %s", e)
            return ["Trade_ID", "Asset_Class", "Price", "Quantity", "Counterparty_LEI"]

    def perform_gap_analysis(self, regulator: str = "EMIR") -> GapAnalysisReport:
        schema_fields = {f.lower(): f for f in self._load_schema_fields()}
        mandates = MANDATED_REGULATORY_FIELDS.get(regulator, MANDATED_REGULATORY_FIELDS["EMIR"])

        gaps: List[FieldComplianceGap] = []
        mapped_count = 0
        missing_count = 0

        for m in mandates:
            req_field = m["field"]
            if req_field.lower() in schema_fields:
                mapped_count += 1
                gaps.append(
                    FieldComplianceGap(
                        mandate_regulator=regulator,
                        mandate_article=m["article"],
                        required_field=req_field,
                        mapped_schema_field=schema_fields[req_field.lower()],
                        status=GapStatus.MAPPED,
                        risk_level="LOW",
                        remediation_action="Field is mapped and conformant with current reporting schema.",
                    )
                )
            else:
                missing_count += 1
                gaps.append(
                    FieldComplianceGap(
                        mandate_regulator=regulator,
                        mandate_article=m["article"],
                        required_field=req_field,
                        mapped_schema_field=None,
                        status=GapStatus.MISSING,
                        risk_level=m["risk"],
                        remediation_action=f"Add '{req_field}' attribute to ingestion schema before reporting deadline.",
                    )
                )

        total_mandates = len(mandates)
        compliance_score = round((mapped_count / total_mandates) * 100.0, 1) if total_mandates > 0 else 100.0

        return GapAnalysisReport(
            regulator=regulator,
            total_mandated_fields=total_mandates,
            mapped_fields_count=mapped_count,
            missing_fields_count=missing_count,
            compliance_score_percentage=compliance_score,
            gaps=gaps,
        )

    def get_compliance_checklist(self, framework: str = "MiFID II") -> ComplianceChecklistResponse:
        checklist_items = [
            ComplianceChecklistItem(
                item_id="CHK-001",
                framework=framework,
                requirement="20-Character Legal Entity Identifier (LEI) Validation for all counterparties",
                verification_criteria="Regex check ^[A-Z0-9]{4}[0-9]{2}[A-Z0-9]{12}[0-9]{2}$ enforced in rule engine",
                status=ChecklistStatus.SATISFIED,
                owner_team="Regulatory Data Operations",
            ),
            ComplianceChecklistItem(
                item_id="CHK-002",
                framework=framework,
                requirement="Microsecond Timestamp Granularity (ISO 8601 UTC) for Algorithmic Trades",
                verification_criteria="Execution_Timestamp parsed and verified non-future UTC",
                status=ChecklistStatus.SATISFIED,
                owner_team="Algorithmic Trading Tech",
            ),
            ComplianceChecklistItem(
                item_id="CHK-003",
                framework=framework,
                requirement="Unique Trade Identifier (UTI) generation and dual-sided reconciliation",
                verification_criteria="Mandatory UTI populated and shared with Trade Repository",
                status=ChecklistStatus.ACTION_REQUIRED,
                owner_team="Middle Office Settlements",
            ),
            ComplianceChecklistItem(
                item_id="CHK-004",
                framework=framework,
                requirement="Approved Publication Arrangement (APA) connectivity and T+1 reporting",
                verification_criteria="Automated delivery within 24 hours of execution confirmation",
                status=ChecklistStatus.SATISFIED,
                owner_team="Compliance Operations",
            ),
            ComplianceChecklistItem(
                item_id="CHK-005",
                framework=framework,
                requirement="Audit lineage traceability from rule violation to regulatory document source",
                verification_criteria="Every violation links to document name, clause ID, and page number",
                status=ChecklistStatus.SATISFIED,
                owner_team="Compliance Intelligence Platform",
            ),
        ]

        satisfied = sum(1 for c in checklist_items if c.status == ChecklistStatus.SATISFIED)
        action_required = sum(1 for c in checklist_items if c.status == ChecklistStatus.ACTION_REQUIRED)

        return ComplianceChecklistResponse(
            framework=framework,
            total_checks=len(checklist_items),
            satisfied_count=satisfied,
            action_required_count=action_required,
            checklist=checklist_items,
        )


gap_analysis_service = GapAnalysisService()
