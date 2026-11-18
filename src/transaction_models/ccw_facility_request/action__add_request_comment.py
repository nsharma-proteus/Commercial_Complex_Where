# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_facility_request
# event_type: action
# function_name: add_request_comment
# action_name: Add Comment
# language: python
# description: Add a comment to the request
# functional_specification: Allowed for members/tenants of the request's UNIT_NO (matched by email), facility team and management, on any status other than 'X' (Cancelled). Require non-blank REMARK. Insert a CCW_FR_UPDATE line with the request's current STATUS and the comment as REMARK; do not change STATUS. Return {"message":"Comment added"}.
# business_logic: Add a comment to the request


def _me(args):
    for k in ('user_email', 'USER_EMAIL', '_user_email'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip()
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('email')):
        return str(u.get('email')).strip()
    return None


def _is_staff():
    roles = [str(r).lower() for r in (api.my_roles() or [])]
    return any(r in ('management', 'facility-team', 'admin', 'func-admin') for r in roles)


def _is_resident(unit, email):
    if not email:
        return False
    e = email.lower()
    for r in db.query('SELECT OWNER_EMAIL FROM ' + db.t('CCW_MEMBER_OWNER') + ' WHERE UNIT_NO = :u', {'u': unit}):
        if str(r['OWNER_EMAIL'] or '').strip().lower() == e:
            return True
    t = db.query_one('SELECT TENANT_EMAIL FROM ' + db.t('CCW_TENANT_PROFILE')
                     + " WHERE UNIT_NO = :u AND TENANT_STATUS = 'A'", {'u': unit})
    return bool(t and str(t['TENANT_EMAIL'] or '').strip().lower() == e)


def run(args):
    no = args.get('REQUEST_NO')
    if is_empty(no):
        return 'Request number is missing'
    req = db.query_one('SELECT STATUS, UNIT_NO, RAISED_BY_EMAIL FROM ' + db.t('CCW_FACILITY_REQUEST')
                       + ' WHERE REQUEST_NO = :n', {'n': no})
    if not req:
        return 'Request not found'
    me = _me(args)
    # If the engine supplies no identity, row security has already limited access to the record.
    if not _is_staff() and me and not _is_resident(req['UNIT_NO'], me):
        return 'Only a member or tenant of this unit, the facility team or management can comment'
    if req['STATUS'] == 'X':
        return 'A cancelled request cannot be commented on'
    remark = args.get('REMARK')
    if is_empty(remark) or not str(remark).strip():
        return 'A comment is required'
    n = db.scalar('SELECT MAX(LINE_NO) FROM ' + db.t('CCW_FR_UPDATE') + ' WHERE REQUEST_NO = :n', {'n': no})
    db.insert('CCW_FR_UPDATE', {'REQUEST_NO': no, 'LINE_NO': int(n or 0) + 1, 'UPDATE_DATE_TIME': now(),
                                'UPDATED_BY': me or req['RAISED_BY_EMAIL'], 'STATUS': req['STATUS'],
                                'REMARK': str(remark).strip()})
    return {'message': 'Comment added'}
