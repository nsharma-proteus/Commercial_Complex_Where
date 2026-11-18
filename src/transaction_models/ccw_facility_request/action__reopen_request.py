# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_facility_request
# event_type: action
# function_name: reopen_request
# action_name: Reopen
# language: python
# description: Reopen a resolved request
# functional_specification: Allowed only for the raiser (signed-in email equals RAISED_BY_EMAIL, case-insensitive) or management. Allowed only when STATUS='R'. Set STATUS='P' (back to In Progress), clear RESOLVED_ON. Insert a CCW_FR_UPDATE line (STATUS='P', REMARK = captured REMARK, or 'Reopened' when blank). Notify the raiser, the assigned team member (EMAIL) and, if the category is Security, the Supervisor(s) by in-app notification and email. Return {"message":"Request reopened"}.
# business_logic: Reopen a resolved request


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
    raiser = str(req['RAISED_BY_EMAIL'] or '').strip().lower()
    me = _me(args) or raiser
    if me.lower() != raiser and not _is_mgmt():
        return 'Only the raiser or management can reopen this request'
    if req['STATUS'] != 'R':
        return 'Only a Resolved request can be reopened'
    remark = args.get('REMARK')
    remark = str(remark).strip() if not is_empty(remark) and str(remark).strip() else 'Reopened'
    db.update('CCW_FACILITY_REQUEST', {'STATUS': 'P', 'RESOLVED_ON': None}, {'REQUEST_NO': no})
    _add_update(no, 'P', remark, me)
    recips = [req['RAISED_BY_EMAIL']]
    if not is_empty(req['ASSIGNED_TO']):
        tm = db.query_one('SELECT EMAIL FROM ' + db.t('CCW_FACILITY_TEAM_MEMBER') + ' WHERE STAFF_CODE = :s',
                          {'s': req['ASSIGNED_TO']})
        if tm and not is_empty(tm['EMAIL']):
            recips.append(tm['EMAIL'])
    if _is_security(req):
        recips += _supervisors()
    body = 'Facility request ' + str(no) + ' (unit ' + str(req['UNIT_NO']) + ') has been reopened.\nRemark: ' + remark
    w = _notify('facility_request_status_changed', no, 'Facility request ' + str(no) + ' reopened', body, recips)
    res = {'message': 'Request reopened'}
    if w:
        res['warnings'] = [w]
    return res
