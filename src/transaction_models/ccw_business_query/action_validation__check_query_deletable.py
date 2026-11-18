# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_business_query
# event_type: action_validation
# function_name: check_query_deletable
# action_name: Delete
# language: python
# description: Delete guard
# functional_specification: Return an error if any row exists in CCW_BQ_RESPONSE for the QUERY_NO ('A query with responses cannot be deleted'). Also return an error unless the signed-in user's email equals RAISED_BY_EMAIL (case-insensitive) or the user holds a management/admin role.
# business_logic: Delete guard


def _me(args):
    for k in ('user_email', 'USER_EMAIL', '_user_email'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip().lower()
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('email')):
        return str(u.get('email')).strip().lower()
    return None


def _is_mgmt():
    roles = [str(r).lower() for r in (api.my_roles() or [])]
    return any(r in ('management', 'admin', 'func-admin') for r in roles)


def run(args):
    query_no = args.get('QUERY_NO')
    if is_empty(query_no):
        return 'Query number is missing'
    q = db.query_one(
        'SELECT RAISED_BY_EMAIL FROM ' + db.t('CCW_BUSINESS_QUERY') + ' WHERE QUERY_NO = :q',
        {'q': query_no})
    if not q:
        return 'Query not found'
    n = db.scalar(
        'SELECT COUNT(*) FROM ' + db.t('CCW_BQ_RESPONSE') + ' WHERE QUERY_NO = :q', {'q': query_no})
    if n and int(n) > 0:
        return 'A query with responses cannot be deleted'
    raiser = (q['RAISED_BY_EMAIL'] or '').strip().lower()
    # If the engine supplies no identity, row security has already limited access to the record.
    me = _me(args) or raiser
    if me != raiser and not _is_mgmt():
        return 'Only the raiser or management can delete this query'
    return None
