# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_member_profile
# event_type: pre_commit
# function_name: validate_primary_owner
# language: python
# description: Exactly one primary joint owner
# functional_specification: Receives {action, txn_id, header, details}. Take the Joint Owners lines (form 2) from details. If there are no lines return {"error": "At least one Joint Owner is required."}. Count lines with IS_PRIMARY_OWNER = 'Y'. If the count is not exactly 1 return {"error": "Exactly one Joint Owner must be marked as Primary Owner."}. Otherwise return nothing.
# business_logic: Exactly one primary joint owner


def run(args):
    details = args.get('details') or {}
    lines = details.get(2)
    if lines is None:
        lines = details.get('2')
    lines = lines or []
    if len(lines) == 0:
        return {'error': 'At least one Joint Owner is required.'}
    primaries = 0
    for ln in lines:
        v = ln.get('IS_PRIMARY_OWNER')
        if v is None:
            v = ln.get('is_primary_owner')
        if v == 'Y':
            primaries += 1
    if primaries != 1:
        return {'error': 'Exactly one Joint Owner must be marked as Primary Owner.'}
    seen = set()
    for ln in lines:
        e = ln.get('OWNER_EMAIL')
        if e is None:
            e = ln.get('owner_email')
        e = (e or '').strip().lower()
        if e:
            if e in seen:
                return {'error': 'Owner email %s is entered on more than one line of this profile.' % e}
            seen.add(e)
    return None
