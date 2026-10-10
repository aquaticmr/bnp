import re
from typing import Any, Dict, Optional, Tuple
from app.engine.operators import OPERATOR_DISPATCH
from app.schemas.rules import ComplianceStatus, FieldCondition, ImpactMatrixItem, RuleDefinition

def interpolate_template(template: str, row: Dict[str, Any]) -> str:

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        val = row.get(var_name)
        if val is None or str(val).lower() in ('nan', 'none', 'null'):
            return '<MISSING>'
        return str(val)
    return re.sub('\\$\\{([a-zA-Z0-9_]+)\\}', replacer, template)

def evaluate_condition(condition: FieldCondition, row: Dict[str, Any]) -> Tuple[bool, Optional[str], Any]:
    field = condition.field
    op_name = condition.operator.value if hasattr(condition.operator, 'value') else str(condition.operator)
    op_func = OPERATOR_DISPATCH.get(op_name)
    if not op_func:
        return (False, field, row.get(field))
    observed_value = row.get(field)
    expected_value = condition.expected_value
    if condition.target_field and condition.target_field in row:
        expected_value = row.get(condition.target_field)
    is_satisfied = op_func(observed_value, expected_value, row)
    return (is_satisfied, field, observed_value)

def evaluate_rule(rule: RuleDefinition, trade_row: Dict[str, Any]) -> Optional[ImpactMatrixItem]:
    trade_id = str(trade_row.get('Trade_ID', trade_row.get('trade_id', 'UNKNOWN_TRADE')))
    if rule.condition:
        passed, failed_field, observed_val = evaluate_condition(rule.condition, trade_row)
        if not passed:
            explanation = interpolate_template(rule.explanation_template, trade_row)
            return ImpactMatrixItem(trade_id=trade_id, rule_id=rule.rule_id, rule_name=rule.name, regulator=rule.regulator, article_citation=rule.article_citation, category=rule.category, severity=rule.severity, status=ComplianceStatus.VIOLATION, failed_field=failed_field, observed_value=observed_val, explanation=explanation)
    if rule.and_conditions:
        for cond in rule.and_conditions:
            passed, failed_field, observed_val = evaluate_condition(cond, trade_row)
            if not passed:
                explanation = interpolate_template(rule.explanation_template, trade_row)
                return ImpactMatrixItem(trade_id=trade_id, rule_id=rule.rule_id, rule_name=rule.name, regulator=rule.regulator, article_citation=rule.article_citation, category=rule.category, severity=rule.severity, status=ComplianceStatus.VIOLATION, failed_field=failed_field, observed_value=observed_val, explanation=explanation)
    if rule.or_conditions:
        any_passed = False
        first_failed_field = None
        first_observed = None
        for cond in rule.or_conditions:
            passed, f_field, obs_val = evaluate_condition(cond, trade_row)
            if passed:
                any_passed = True
                break
            if first_failed_field is None:
                first_failed_field = f_field
                first_observed = obs_val
        if not any_passed:
            explanation = interpolate_template(rule.explanation_template, trade_row)
            return ImpactMatrixItem(trade_id=trade_id, rule_id=rule.rule_id, rule_name=rule.name, regulator=rule.regulator, article_citation=rule.article_citation, category=rule.category, severity=rule.severity, status=ComplianceStatus.VIOLATION, failed_field=first_failed_field, observed_value=first_observed, explanation=explanation)
    return None