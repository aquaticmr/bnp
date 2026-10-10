import pytest
from app.engine.operators import (
    op_equals,
    op_in_set,
    op_lei_valid,
    op_positive_number,
    op_iso8601_valid,
    op_date_after,
)
from app.engine.evaluator import evaluate_rule, interpolate_template
from app.engine.rule_loader import default_rule_loader
from app.schemas.rules import (
    ComplianceStatus,
    ConditionOperator,
    FieldCondition,
    RuleDefinition,
    SeverityLevel,
)


def test_operator_lei_valid():
    # Valid ISO 17442 LEI (20 alphanumeric chars)
    assert op_lei_valid("5493006MHB84DD0ZWV18", None, {}) is True
    assert op_lei_valid("7245009UXRIGIRYENR60", None, {}) is True
    # Invalid LEIs
    assert op_lei_valid("TOO_SHORT", None, {}) is False
    assert op_lei_valid("5493006MHB84DD0ZWV1!", None, {}) is False  # special char
    assert op_lei_valid("", None, {}) is False
    assert op_lei_valid(None, None, {}) is False


def test_operator_positive_number():
    assert op_positive_number(100.50, None, {}) is True
    assert op_positive_number("0.05", None, {}) is True
    assert op_positive_number(0, None, {}) is False
    assert op_positive_number(-15.20, None, {}) is False
    assert op_positive_number(None, None, {}) is False


def test_operator_iso8601_valid():
    assert op_iso8601_valid("2026-03-15T10:15:30Z", None, {}) is True
    assert op_iso8601_valid("2026-03-15 10:15:30", None, {}) is True
    assert op_iso8601_valid("NOT_A_TIMESTAMP", None, {}) is False


def test_operator_date_after():
    row = {"Execution_Timestamp": "2026-03-15T10:00:00Z"}
    assert op_date_after("2026-06-01", "Execution_Timestamp", row) is True
    assert op_date_after("2025-01-01", "Execution_Timestamp", row) is False


def test_template_interpolation():
    template = "Price ${Price} is invalid for trade ${Trade_ID}"
    row = {"Price": -50.2, "Trade_ID": "TRD-999"}
    result = interpolate_template(template, row)
    assert result == "Price -50.2 is invalid for trade TRD-999"


def test_evaluate_rule_compliant():
    rule = RuleDefinition(
        rule_id="EMIR-TEST-01",
        name="Valid LEI Test",
        regulator="EMIR",
        article_citation="Article 9",
        category="REPORTING",
        severity=SeverityLevel.HIGH,
        description="Must have valid LEI",
        condition=FieldCondition(field="Counterparty_LEI", operator=ConditionOperator.LEI_VALID),
        explanation_template="Invalid LEI: ${Counterparty_LEI}",
    )
    compliant_trade = {
        "Trade_ID": "T1",
        "Counterparty_LEI": "5493006MHB84DD0ZWV18",
    }
    violation = evaluate_rule(rule, compliant_trade)
    assert violation is None


def test_evaluate_rule_violation():
    rule = RuleDefinition(
        rule_id="MIFID-TEST-02",
        name="Positive Price Test",
        regulator="MiFID II",
        article_citation="RTS 22",
        category="PRICING",
        severity=SeverityLevel.HIGH,
        description="Price must be positive",
        condition=FieldCondition(field="Price", operator=ConditionOperator.POSITIVE_NUMBER),
        explanation_template="Price negative: ${Price}",
    )
    invalid_trade = {
        "Trade_ID": "T2",
        "Price": -10.5,
    }
    violation = evaluate_rule(rule, invalid_trade)
    assert violation is not None
    assert violation.trade_id == "T2"
    assert violation.status == ComplianceStatus.VIOLATION
    assert violation.failed_field == "Price"
    assert violation.observed_value == -10.5
    assert "Price negative: -10.5" in violation.explanation


def test_load_regulatory_rules_catalog():
    catalog = default_rule_loader.get_catalog()
    assert catalog.total_rules >= 5
    assert "EMIR" in catalog.regulators
    assert "MiFID II" in catalog.regulators
