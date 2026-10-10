from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SeverityLevel(str, Enum):
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'

class ComplianceStatus(str, Enum):
    VIOLATION = 'VIOLATION'
    COMPLIANT = 'COMPLIANT'

class ConditionOperator(str, Enum):
    EQUALS = 'equals'
    NOT_EQUALS = 'not_equals'
    EXISTS = 'exists'
    NOT_NULL = 'not_null'
    IN_SET = 'in_set'
    NOT_IN_SET = 'not_in_set'
    GREATER_THAN = 'greater_than'
    LESS_THAN = 'less_than'
    GREATER_THAN_OR_EQUAL = 'greater_than_or_equal'
    LESS_THAN_OR_EQUAL = 'less_than_or_equal'
    REGEX_MATCH = 'regex_match'
    LEI_VALID = 'lei_valid'
    ISO8601_VALID = 'iso8601_valid'
    POSITIVE_NUMBER = 'positive_number'
    DATE_AFTER = 'date_after'
    DATE_BEFORE = 'date_before'

class FieldCondition(BaseModel):
    field: str
    operator: ConditionOperator
    expected_value: Optional[Any] = None
    target_field: Optional[str] = None

class RuleDefinition(BaseModel):
    rule_id: str = Field(..., description='Unique rule code, e.g., EMIR-R4.2')
    name: str = Field(..., description='Human-readable rule title')
    regulator: str = Field(..., description='Applicable regulator, e.g., EMIR, MiFID II, Dodd-Frank')
    article_citation: str = Field(..., description='Regulatory clause or article citation')
    category: str = Field(default='TRANSACTION_REPORTING')
    severity: SeverityLevel = Field(default=SeverityLevel.HIGH)
    description: str
    condition: Optional[FieldCondition] = None
    and_conditions: Optional[List[FieldCondition]] = None
    or_conditions: Optional[List[FieldCondition]] = None
    explanation_template: str = Field(..., description='Template for violation message with ${fieldName} placeholders')

class RuleCatalog(BaseModel):
    version: str = '1.0.0'
    regulators: List[str]
    total_rules: int
    rules: List[RuleDefinition]

class ImpactMatrixItem(BaseModel):
    trade_id: str
    rule_id: str
    rule_name: str
    regulator: str
    article_citation: str
    category: str
    severity: SeverityLevel
    status: ComplianceStatus
    failed_field: Optional[str] = None
    observed_value: Optional[Any] = None
    explanation: str

class ImpactMatrixFilterParams(BaseModel):
    trade_id: Optional[str] = None
    rule_id: Optional[str] = None
    regulator: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    status: Optional[ComplianceStatus] = None

class ImpactMatrixResponse(BaseModel):
    total_records: int
    total_violations: int
    compliant_trades: int
    non_compliant_trades: int
    violations_by_severity: Dict[str, int]
    violations_by_regulator: Dict[str, int]
    page: int
    page_size: int
    total_pages: int
    items: List[ImpactMatrixItem]