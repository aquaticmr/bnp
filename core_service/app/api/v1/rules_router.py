import io
from pathlib import Path
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from app.core.config import settings
from app.core.security import verify_bearer_token
from app.engine.impact_matrix import impact_engine
from app.engine.rule_loader import default_rule_loader
from app.schemas.rules import (
    ComplianceStatus,
    ImpactMatrixFilterParams,
    ImpactMatrixResponse,
    RuleCatalog,
    SeverityLevel,
)

router = APIRouter(prefix="/rules", tags=["Rules Engine & Impact Domain"])


def _load_default_trades_df() -> pd.DataFrame:
    trades_path = settings.TRADES_PATH
    if trades_path.exists():
        try:
            return pd.read_csv(trades_path)
        except Exception:
            pass
    # Generate in-memory fallback DataFrame if file is not found
    return pd.DataFrame([
        {
            "Trade_ID": "TRD-1001",
            "Asset_Class": "EQUITY",
            "Counterparty_LEI": "5493006MHB84DD0ZWV18",
            "Price": 154.20,
            "Quantity": 1000,
            "Currency": "EUR",
            "Venue": "XOFF",
            "Execution_Timestamp": "2026-03-15T10:15:30Z",
        },
        {
            "Trade_ID": "TRD-1002",
            "Asset_Class": "COMMODITY",
            "Counterparty_LEI": "INVALID_LEI_123",
            "Price": -50.00,
            "Quantity": 500,
            "Currency": "USD",
            "Venue": "XLON",
            "Execution_Timestamp": "2026-03-15T11:00:00Z",
        },
    ])


@router.get("", response_model=RuleCatalog, summary="List active regulatory rules")
def list_rules(
    _auth: bool = Depends(verify_bearer_token),
) -> RuleCatalog:
    return default_rule_loader.get_catalog()


@router.get("/impact-matrix", response_model=ImpactMatrixResponse, summary="Compute or fetch trade-to-rule Impact Matrix")
def get_impact_matrix(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=500, description="Page size"),
    sort_by: str = Query(default="trade_id", description="Field to sort by"),
    sort_desc: bool = Query(default=False, description="Sort descending"),
    trade_id: Optional[str] = Query(default=None, description="Filter by Trade ID"),
    rule_id: Optional[str] = Query(default=None, description="Filter by Rule ID"),
    regulator: Optional[str] = Query(default=None, description="Filter by Regulator"),
    severity: Optional[SeverityLevel] = Query(default=None, description="Filter by Severity"),
    status: Optional[ComplianceStatus] = Query(default=None, description="Filter by Status"),
    _auth: bool = Depends(verify_bearer_token),
) -> ImpactMatrixResponse:
    rules = default_rule_loader.load_rules()
    trades_df = _load_default_trades_df()

    filters = ImpactMatrixFilterParams(
        trade_id=trade_id,
        rule_id=rule_id,
        regulator=regulator,
        severity=severity,
        status=status,
    )

    return impact_engine.evaluate_dataframe(
        df=trades_df,
        rules=rules,
        filters=filters,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


@router.post("/impact-matrix/upload", response_model=ImpactMatrixResponse, summary="Evaluate uploaded trade CSV file")
async def evaluate_uploaded_trades(
    file: UploadFile = File(..., description="CSV file containing trade records"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    _auth: bool = Depends(verify_bearer_token),
) -> ImpactMatrixResponse:
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a CSV format",
        )

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV: {str(e)}",
        )

    rules = default_rule_loader.load_rules()
    return impact_engine.evaluate_dataframe(
        df=df,
        rules=rules,
        page=page,
        page_size=page_size,
    )


@router.get("/impact-matrix/export-csv", summary="Download Impact Matrix as CSV")
def export_impact_matrix_csv(
    trade_id: Optional[str] = Query(default=None),
    rule_id: Optional[str] = Query(default=None),
    regulator: Optional[str] = Query(default=None),
    severity: Optional[SeverityLevel] = Query(default=None),
    _auth: bool = Depends(verify_bearer_token),
):
    rules = default_rule_loader.load_rules()
    trades_df = _load_default_trades_df()

    filters = ImpactMatrixFilterParams(
        trade_id=trade_id,
        rule_id=rule_id,
        regulator=regulator,
        severity=severity,
    )

    # Evaluate all without page restriction for export
    full_report = impact_engine.evaluate_dataframe(
        df=trades_df,
        rules=rules,
        filters=filters,
        page=1,
        page_size=100000,
    )

    csv_data = impact_engine.export_csv(full_report.items)

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=reg_iris_impact_matrix.csv"
        },
    )
