import re
from datetime import datetime
from typing import Any, Callable, Dict, Optional
LEI_PATTERN = re.compile('^[A-Z0-9]{4}[0-9]{2}[A-Z0-9]{12}[0-9]{2}$', re.IGNORECASE)

def op_equals(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    if val is None or expected is None:
        return val == expected
    return str(val).strip().lower() == str(expected).strip().lower()

def op_not_equals(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    return not op_equals(val, expected, row)

def op_exists(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    return val is not None

def op_not_null(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    if val is None:
        return False
    str_val = str(val).strip()
    return str_val != '' and str_val.lower() not in ('null', 'none', 'nan')

def op_in_set(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    if val is None or expected is None:
        return False
    if isinstance(expected, (list, tuple, set)):
        target_set = {str(x).strip().lower() for x in expected}
        return str(val).strip().lower() in target_set
    return str(val).strip().lower() == str(expected).strip().lower()

def op_not_in_set(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    return not op_in_set(val, expected, row)

def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def op_greater_than(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    num = _to_float(val)
    exp = _to_float(expected)
    if num is None or exp is None:
        return False
    return num > exp

def op_less_than(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    num = _to_float(val)
    exp = _to_float(expected)
    if num is None or exp is None:
        return False
    return num < exp

def op_greater_than_or_equal(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    num = _to_float(val)
    exp = _to_float(expected)
    if num is None or exp is None:
        return False
    return num >= exp

def op_less_than_or_equal(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    num = _to_float(val)
    exp = _to_float(expected)
    if num is None or exp is None:
        return False
    return num <= exp

def op_positive_number(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    num = _to_float(val)
    if num is None:
        return False
    return num > 0.0

def op_regex_match(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    if val is None or not expected:
        return False
    try:
        return bool(re.search(str(expected), str(val)))
    except re.error:
        return False

def op_lei_valid(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    if not val:
        return False
    cleaned = str(val).strip()
    return bool(LEI_PATTERN.match(cleaned))

def _parse_timestamp(val: Any) -> Optional[datetime]:
    if not val:
        return None
    str_val = str(val).strip()
    formats = ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(str_val.replace('Z', '+0000') if 'Z' in str_val and '%z' in fmt else str_val, fmt)
        except (ValueError, TypeError):
            continue
    try:
        from dateutil import parser
        return parser.parse(str_val)
    except Exception:
        return None

def op_iso8601_valid(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    return _parse_timestamp(val) is not None

def op_date_after(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    dt1 = _parse_timestamp(val)
    if not dt1:
        return False
    ref_val = row.get(str(expected)) if str(expected) in row else expected
    dt2 = _parse_timestamp(ref_val)
    if not dt2:
        return False
    if dt1.tzinfo and (not dt2.tzinfo):
        dt1 = dt1.replace(tzinfo=None)
    elif dt2.tzinfo and (not dt1.tzinfo):
        dt2 = dt2.replace(tzinfo=None)
    return dt1 > dt2

def op_date_before(val: Any, expected: Any, row: Dict[str, Any]) -> bool:
    dt1 = _parse_timestamp(val)
    if not dt1:
        return False
    ref_val = row.get(str(expected)) if str(expected) in row else expected
    dt2 = _parse_timestamp(ref_val)
    if not dt2:
        return False
    if dt1.tzinfo and (not dt2.tzinfo):
        dt1 = dt1.replace(tzinfo=None)
    elif dt2.tzinfo and (not dt1.tzinfo):
        dt2 = dt2.replace(tzinfo=None)
    return dt1 < dt2
OPERATOR_DISPATCH: Dict[str, Callable[[Any, Any, Dict[str, Any]], bool]] = {'equals': op_equals, 'not_equals': op_not_equals, 'exists': op_exists, 'not_null': op_not_null, 'in_set': op_in_set, 'not_in_set': op_not_in_set, 'greater_than': op_greater_than, 'less_than': op_less_than, 'greater_than_or_equal': op_greater_than_or_equal, 'less_than_or_equal': op_less_than_or_equal, 'positive_number': op_positive_number, 'regex_match': op_regex_match, 'lei_valid': op_lei_valid, 'iso8601_valid': op_iso8601_valid, 'date_after': op_date_after, 'date_before': op_date_before}