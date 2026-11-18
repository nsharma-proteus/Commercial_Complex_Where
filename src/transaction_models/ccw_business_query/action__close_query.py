# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_business_query
# event_type: action
# function_name: close_query
# action_name: Close
# language: python
# description: Close the query
# functional_specification: Allowed only to the raiser (signed-in email equals RAISED_BY_EMAIL, case-insensitive) or a management/admin role; otherwise error. Refuse unless STATUS='O'. Set STATUS='C', CLOSURE_REMARK from the payload, CLOSED_ON = now on CCW_BUSINESS_QUERY. Return {"message":"Query closed"}.
# business_logic: Close the query


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
        'SELECT STATUS, RAISED_BY_EMAIL FROM ' + db.t('CCW_BUSINESS_QUERY') + ' WHERE QUERY_NO = :q',
        {'q': query_no})
    if not q:
        return 'Query not found'
    raiser = (q['RAISED_BY_EMAIL'] or '').strip().lower()
    # If the engine supplies no identity, row security has already limited access to the record.
    me = _me(args) or raiser
    if me != raiser and not _is_mgmt():
        return 'Only the raiser or management can close this query'
    if q['STATUS'] != 'O':
        return 'Only an open query can be closed'
    db.update('CCW_BUSINESS_QUERY',
              {'STATUS': 'C', 'CLOSURE_REMARK': args.get('CLOSURE_REMARK') or None, 'CLOSED_ON': now()},
              {'QUERY_NO': query_no})
    return {'message': 'Query closed'}
