import pytest
from app.engine.impact_matrix import impact_engine
from app.schemas.rules import (
    ConditionOperator,
    FieldCondition,
    ImpactMatrixFilterParams,
    RuleDefinition,
    SeverityLevel,
)


@pytest.fixture
def sample_test_rules():
    return [
        RuleDefinition(
            rule_id="RULE-LEI",
            name="LEI Validation",
            regulator="EMIR",
            article_citation="Article 9",
            category="IDENTIFICATION",
            severity=SeverityLevel.HIGH,
            description="Check LEI format",
            condition=FieldCondition(field="Counterparty_LEI", operator=ConditionOperator.LEI_VALID),
            explanation_template="Bad LEI ${Counterparty_LEI}",
        ),
        RuleDefinition(
            rule_id="RULE-PRICE",
            name="Positive Price",
            regulator="MiFID II",
            article_citation="RTS 22",
            category="PRICING",
            severity=SeverityLevel.MEDIUM,
            description="Price must be positive",
            condition=FieldCondition(field="Price", operator=ConditionOperator.POSITIVE_NUMBER),
            explanation_template="Bad Price ${Price}",
        ),
    ]


@pytest.fixture
def sample_trades():
    return [
        {"Trade_ID": "T1", "Counterparty_LEI": "5493006MHB84DD0ZWV18", "Price": 100.0},  # Compliant
        {"Trade_ID": "T2", "Counterparty_LEI": "INVALID_LEI", "Price": 50.0},             # 1 violation (LEI)
        {"Trade_ID": "T3", "Counterparty_LEI": "INVALID_LEI", "Price": -10.0},            # 2 violations (LEI + Price)
    ]


def test_impact_matrix_computation(sample_test_rules, sample_trades):
    resp = impact_engine.evaluate_trades(trades=sample_trades, rules=sample_test_rules)

    assert resp.total_violations == 3
    assert resp.compliant_trades == 1
    assert resp.non_compliant_trades == 2
    assert resp.violations_by_severity[SeverityLevel.HIGH.value] == 2
    assert resp.violations_by_severity[SeverityLevel.MEDIUM.value] == 1


def test_impact_matrix_filtering(sample_test_rules, sample_trades):
    filters = ImpactMatrixFilterParams(severity=SeverityLevel.HIGH)
    resp = impact_engine.evaluate_trades(
        trades=sample_trades,
        rules=sample_test_rules,
        filters=filters,
    )
    assert resp.total_records == 2
    for item in resp.items:
        assert item.severity == SeverityLevel.HIGH


def test_impact_matrix_csv_export(sample_test_rules, sample_trades):
    resp = impact_engine.evaluate_trades(trades=sample_trades, rules=sample_test_rules)
    csv_text = impact_engine.export_csv(resp.items)

    assert "Trade_ID,Rule_ID,Rule_Name" in csv_text
    assert "T2" in csv_text
    assert "T3" in csv_text
    assert "VIOLATION" in csv_text
