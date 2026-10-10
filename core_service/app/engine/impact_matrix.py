import io
import csv
import logging
from typing import Any, Dict, List, Optional
import pandas as pd
from app.engine.evaluator import evaluate_rule
from app.schemas.rules import (
    ComplianceStatus,
    ImpactMatrixFilterParams,
    ImpactMatrixItem,
    ImpactMatrixResponse,
    RuleDefinition,
    SeverityLevel,
)

logger = logging.getLogger(__name__)


class ImpactMatrixEngine:
    def evaluate_trades(
        self,
        trades: List[Dict[str, Any]],
        rules: List[RuleDefinition],
        filters: Optional[ImpactMatrixFilterParams] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "trade_id",
        sort_desc: bool = False,
    ) -> ImpactMatrixResponse:
        """
        Evaluates a collection of trade dictionaries against regulatory rules
        and produces the Impact Matrix report with pagination, statistics, and filtering.
        """
        violations: List[ImpactMatrixItem] = []
        trade_status_map: Dict[str, bool] = {}  # trade_id -> has_violations

        # 1. Run data-driven rule evaluation for every trade against every active rule
        for trade in trades:
            trade_id = str(trade.get("Trade_ID", trade.get("trade_id", "UNKNOWN")))
            if trade_id not in trade_status_map:
                trade_status_map[trade_id] = False

            for rule in rules:
                violation = evaluate_rule(rule, trade)
                if violation:
                    violations.append(violation)
                    trade_status_map[trade_id] = True

        total_trades = len(trade_status_map)
        non_compliant_trades = sum(1 for has_err in trade_status_map.values() if has_err)
        compliant_trades = total_trades - non_compliant_trades

        # 2. Compute violation distributions
        violations_by_severity: Dict[str, int] = {
            SeverityLevel.HIGH.value: 0,
            SeverityLevel.MEDIUM.value: 0,
            SeverityLevel.LOW.value: 0,
        }
        violations_by_regulator: Dict[str, int] = {}

        for v in violations:
            sev_key = v.severity.value if hasattr(v.severity, "value") else str(v.severity)
            violations_by_severity[sev_key] = violations_by_severity.get(sev_key, 0) + 1
            violations_by_regulator[v.regulator] = violations_by_regulator.get(v.regulator, 0) + 1

        # 3. Apply filters
        filtered_items = violations
        if filters:
            if filters.trade_id:
                filtered_items = [i for i in filtered_items if filters.trade_id.lower() in i.trade_id.lower()]
            if filters.rule_id:
                filtered_items = [i for i in filtered_items if filters.rule_id.lower() in i.rule_id.lower()]
            if filters.regulator:
                filtered_items = [i for i in filtered_items if filters.regulator.lower() in i.regulator.lower()]
            if filters.severity:
                filtered_items = [i for i in filtered_items if i.severity == filters.severity]

        # 4. Sorting
        def sort_key(item: ImpactMatrixItem):
            val = getattr(item, sort_by, None)
            return str(val or "")

        filtered_items = sorted(filtered_items, key=sort_key, reverse=sort_desc)

        # 5. Pagination
        total_records = len(filtered_items)
        total_pages = max(1, (total_records + page_size - 1) // page_size) if total_records > 0 else 1
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = filtered_items[start_idx:end_idx]

        return ImpactMatrixResponse(
            total_records=total_records,
            total_violations=len(violations),
            compliant_trades=compliant_trades,
            non_compliant_trades=non_compliant_trades,
            violations_by_severity=violations_by_severity,
            violations_by_regulator=violations_by_regulator,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=paginated_items,
        )

    def evaluate_dataframe(
        self,
        df: pd.DataFrame,
        rules: List[RuleDefinition],
        filters: Optional[ImpactMatrixFilterParams] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "trade_id",
        sort_desc: bool = False,
    ) -> ImpactMatrixResponse:
        trades = df.to_dict(orient="records")
        return self.evaluate_trades(trades, rules, filters, page, page_size, sort_by, sort_desc)

    def export_csv(self, violations: List[ImpactMatrixItem]) -> str:
        """
        Exports violation matrix items into standard CSV format for compliance reporting.
        """
        output = io.StringIO()
        fieldnames = [
            "Trade_ID",
            "Rule_ID",
            "Rule_Name",
            "Regulator",
            "Article_Citation",
            "Category",
            "Severity",
            "Status",
            "Failed_Field",
            "Observed_Value",
            "Explanation",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for item in violations:
            writer.writerow({
                "Trade_ID": item.trade_id,
                "Rule_ID": item.rule_id,
                "Rule_Name": item.rule_name,
                "Regulator": item.regulator,
                "Article_Citation": item.article_citation,
                "Category": item.category,
                "Severity": item.severity.value if hasattr(item.severity, "value") else str(item.severity),
                "Status": item.status.value if hasattr(item.status, "value") else str(item.status),
                "Failed_Field": item.failed_field or "",
                "Observed_Value": str(item.observed_value) if item.observed_value is not None else "",
                "Explanation": item.explanation,
            })

        return output.getvalue()


impact_engine = ImpactMatrixEngine()
