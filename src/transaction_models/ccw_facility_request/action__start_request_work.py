# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_facility_request
# event_type: action
# function_name: start_request_work
# action_name: Start Work
# language: python
# description: Start work on the request
# functional_specification: Facility team / management only. Allowed only when STATUS='A'. Set STATUS='P'. Insert a CCW_FR_UPDATE line (STATUS='P', REMARK='Work started'). Notify the raiser by in-app notification and email, and the Supervisor(s) (CCW_FACILITY_TEAM_MEMBER ROLE='S', STATUS='A') if the category is Security. Return {"message":"Work started"}.
# business_logic: Start work on the request


def _me(args):
    for k in ('user_email', 'USER_EMAIL', '_user_email'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip()
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('email')):
        return str(u.get('email')).strip()
    return None


def _roles():
    return [str(r).lower() for r in (api.my_roles() or [])]


def _is_staff():
    return any(r in ('management', 'facility-team', 'admin', 'func-admin') for r in _roles())


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
    if not _is_staff():
        return 'Only the facility team or management can start work'
    if req['STATUS'] != 'A':
        return 'Work can be started only on an Assigned request'
    me = _me(args) or 'system'
    db.update('CCW_FACILITY_REQUEST', {'STATUS': 'P'}, {'REQUEST_NO': no})
    _add_update(no, 'P', 'Work started', me)
    recips = [req['RAISED_BY_EMAIL']]
    if _is_security(req):
        recips += _supervisors()
    body = 'Work has started on facility request ' + str(no) + ' (unit ' + str(req['UNIT_NO']) + ').'
    w = _notify('facility_request_status_changed', no, 'Facility request ' + str(no) + ': work started', body, recips)
    res = {'message': 'Work started'}
    if w:
        res['warnings'] = [w]
    return res
