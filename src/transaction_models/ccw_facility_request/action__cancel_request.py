# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_facility_request
# event_type: action
# function_name: cancel_request
# action_name: Cancel
# language: python
# description: Cancel an Open or Assigned request
# functional_specification: Allowed for the raiser's unit (members/tenants of UNIT_NO matched by email) or management, when STATUS is 'O' or 'A'. Set STATUS='X'. Insert a CCW_FR_UPDATE line (STATUS='X', REMARK = captured REMARK or 'Cancelled'). Notify the raiser, the assigned team member if any, and the Supervisor(s) if the category is Security. Return {"message":"Request cancelled"}.
# business_logic: Cancel an Open or Assigned request


def _me(args):
    for k in ('user_email', 'USER_EMAIL', '_user_email'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip()
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('email')):
        return str(u.get('email')).strip()
    return None


def _is_mgmt():
    roles = [str(r).lower() for r in (api.my_roles() or [])]
    return any(r in ('management', 'admin', 'func-admin') for r in roles)


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


def _is_security(req):
    code = str(req['REQUEST_CATEGORY'] or '').strip().lower()
    if code == 'security':
        return True
    c = db.query_one('SELECT NAME FROM ' + db.t('CCW_FACILITY_REQ_CATEGORY') + ' WHERE REQUEST_CATEGORY_CODE = :c',
                     {'c': req['REQUEST_CATEGORY']})
    return bool(c and str(c['NAME'] or '').strip().lower() == 'security')


def _supervisors():
    out = []
    for r in db.query('SELECT EMAIL FROM ' + db.t('CCW_FACILITY_TEAM_MEMBER') + " WHERE ROLE = 'S' AND STATUS = 'A'"):
        if not is_empty(r['EMAIL']):
            out.append(str(r['EMAIL']).strip())
    return out


def _add_update(no, status, remark, me):
    n = db.scalar('SELECT MAX(LINE_NO) FROM ' + db.t('CCW_FR_UPDATE') + ' WHERE REQUEST_NO = :n', {'n': no})
    db.insert('CCW_FR_UPDATE', {'REQUEST_NO': no, 'LINE_NO': int(n or 0) + 1, 'UPDATE_DATE_TIME': now(),
                                'UPDATED_BY': me, 'STATUS': status, 'REMARK': remark})


def _notify(event, no, subject, body, recips):
    seen = set()
    out = []
    for e in recips:
        e = (e or '').strip()
        if e and e.lower() not in seen:
            seen.add(e.lower())
            out.append(e)
    if not out:
        return None
    try:
        api.emit_event(event, {'request_no': no, 'subject': subject, 'message': body, 'recipients': out})
    except Exception as ex:
        return {'code': 'FRNOTIFY', 'type': 'W', 'message': 'Saved but notification failed: ' + str(ex)}
    return None


def run(args):
    no = args.get('REQUEST_NO')
    if is_empty(no):
        return 'Request number is missing'
    req = db.query_one('SELECT * FROM ' + db.t('CCW_FACILITY_REQUEST') + ' WHERE REQUEST_NO = :n', {'n': no})
    if not req:
        return 'Request not found'
    me = _me(args)
    # If the engine supplies no identity, row security has already limited access to the record.
    if not _is_mgmt() and me and not _is_resident(req['UNIT_NO'], me):
        return 'Only a member or tenant of this unit, or management, can cancel this request'
    if req['STATUS'] not in ('O', 'A'):
        return 'Only an Open or Assigned request can be cancelled'
    remark = args.get('REMARK')
    remark = str(remark).strip() if not is_empty(remark) and str(remark).strip() else 'Cancelled'
    db.update('CCW_FACILITY_REQUEST', {'STATUS': 'X'}, {'REQUEST_NO': no})
    _add_update(no, 'X', remark, me or req['RAISED_BY_EMAIL'])
    recips = [req['RAISED_BY_EMAIL']]
    if not is_empty(req['ASSIGNED_TO']):
        tm = db.query_one('SELECT EMAIL FROM ' + db.t('CCW_FACILITY_TEAM_MEMBER') + ' WHERE STAFF_CODE = :s',
                          {'s': req['ASSIGNED_TO']})
        if tm and not is_empty(tm['EMAIL']):
            recips.append(tm['EMAIL'])
    if _is_security(req):
        recips += _supervisors()
    body = 'Facility request ' + str(no) + ' (unit ' + str(req['UNIT_NO']) + ') has been cancelled.\nReason: ' + remark
    w = _notify('facility_request_status_changed', no, 'Facility request ' + str(no) + ' cancelled', body, recips)
    res = {'message': 'Request cancelled'}
    if w:
        res['warnings'] = [w]
    return res
