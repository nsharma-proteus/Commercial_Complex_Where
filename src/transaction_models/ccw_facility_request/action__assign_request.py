# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_facility_request
# event_type: action
# function_name: assign_request
# action_name: Assign
# language: python
# description: Assign the request to a facility team member
# functional_specification: For facility team / management users only. Allowed only when STATUS='O'. ASSIGNED_TO (saved on the record) must be non-blank and an active CCW_FACILITY_TEAM_MEMBER (STATUS='A'), else error. Set STATUS='A'. Insert a CCW_FR_UPDATE line (next LINE_NO, UPDATE_DATE_TIME=now, UPDATED_BY=signed-in user email, STATUS='A', REMARK='Assigned to <STAFF_NAME>'). Notify the raiser (RAISED_BY_EMAIL) by in-app notification and email; notify the assigned team member (EMAIL of CCW_FACILITY_TEAM_MEMBER). If the request category is Security (REQUEST_CATEGORY or its NAME equals 'Security', case-insensitive) also notify every active team member with ROLE='S' (Supervisor). Return {"message":"Request assigned"}.
# business_logic: Assign the request to a facility team member


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
        return 'Only the facility team or management can assign a request'
    if req['STATUS'] != 'O':
        return 'Only an Open request can be assigned'
    staff = req['ASSIGNED_TO']
    if is_empty(staff) or not str(staff).strip():
        return 'Assigned To is required to assign the request'
    tm = db.query_one('SELECT STAFF_NAME, EMAIL, STATUS FROM ' + db.t('CCW_FACILITY_TEAM_MEMBER')
                      + ' WHERE STAFF_CODE = :s', {'s': str(staff).strip()})
    if not tm or tm['STATUS'] != 'A':
        return 'Assigned To must be an active Facility Team Member'
    me = _me(args) or 'system'
    db.update('CCW_FACILITY_REQUEST', {'STATUS': 'A'}, {'REQUEST_NO': no})
    _add_update(no, 'A', 'Assigned to ' + str(tm['STAFF_NAME']), me)
    warns = []
    w = _notify('facility_request_status_changed', no, 'Facility request ' + str(no) + ' assigned',
                'Your facility request ' + str(no) + ' has been assigned to ' + str(tm['STAFF_NAME']) + '.',
                [req['RAISED_BY_EMAIL']])
    if w:
        warns.append(w)
    staff_recips = [tm['EMAIL']]
    if _is_security(req):
        staff_recips += _supervisors()
    body = ('Facility request ' + str(no) + ' has been assigned to ' + str(tm['STAFF_NAME'])
            + '.\nUnit: ' + str(req['UNIT_NO']) + '\nPriority: ' + str(req['PRIORITY'])
            + '\nDescription: ' + str(req['DESCRIPTION'] or ''))
    w = _notify('facility_request_assigned', no, 'Facility request ' + str(no) + ' assigned', body, staff_recips)
    if w:
        warns.append(w)
    res = {'message': 'Request assigned'}
    if warns:
        res['warnings'] = warns[:1]
    return res
