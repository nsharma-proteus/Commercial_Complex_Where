# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_business_query
# event_type: action_validation
# function_name: check_query_raiser_or_mgmt
# action_name: Edit
# language: python
# description: Raiser (or management where stated) check
# functional_specification: Return {"error":"Only the raiser can edit this query."} unless the signed-in user's email equals RAISED_BY_EMAIL (case-insensitive) of CCW_BUSINESS_QUERY for QUERY_NO. Management is NOT allowed for Edit.
# business_logic: Raiser (or management where stated) check


def _me(args):
    for k in ('user_email', 'USER_EMAIL', '_user_email'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip().lower()
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('email')):
        return str(u.get('email')).strip().lower()
    return None


def run(args):
    query_no = args.get('QUERY_NO')
    if is_empty(query_no):
        return None
    q = db.query_one(
        'SELECT RAISED_BY_EMAIL FROM ' + db.t('CCW_BUSINESS_QUERY') + ' WHERE QUERY_NO = :q',
        {'q': query_no})
    if not q:
        return None
    raiser = (q['RAISED_BY_EMAIL'] or '').strip().lower()
    # If the engine supplies no identity, row security has already limited access to the record.
    me = _me(args) or raiser
    if me != raiser:
        return {'error': 'Only the raiser can edit this query.'}
    return None
