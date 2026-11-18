# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_member_profile
# event_type: pre_commit
# function_name: validate_member_categories
# language: python
# description: No repeated additional business category in the grid
# functional_specification: Receives {action, txn_id, header, details}. Other Categories lines are form 3 of details. Error if the same CATEGORY_CODE (trimmed, case-insensitive) appears on two lines, or equals header BUSINESS_CATEGORY. Otherwise return nothing.
# business_logic: No repeated additional business category in the grid


def _val(row, name):
    v = row.get(name)
    if v is None:
        v = row.get(name.lower())
    return (str(v).strip() if v is not None else '')


def run(args):
    header = args.get('header') or {}
    details = args.get('details') or {}
    lines = details.get(3)
    if lines is None:
        lines = details.get('3')
    lines = lines or []
    primary = _val(header, 'BUSINESS_CATEGORY').lower()
    seen = set()
    for ln in lines:
        code = _val(ln, 'CATEGORY_CODE')
        if not code:
            continue
        key = code.lower()
        if key in seen:
            return {'error': 'Business category %s is listed more than once under Additional Business Categories.' % code}
        seen.add(key)
        if primary and key == primary:
            return {'error': 'Business category %s is already the primary Business Category.' % code}
    return None
