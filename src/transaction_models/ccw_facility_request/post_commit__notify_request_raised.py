# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_facility_request
# event_type: post_commit
# function_name: notify_request_raised
# language: python
# description: Notify the supervisor of a Security request
# functional_specification: On action='add' only: if the request category is Security (REQUEST_CATEGORY or its CCW_FACILITY_REQ_CATEGORY.NAME equals 'Security', case-insensitive), send an in-app notification and email to every active CCW_FACILITY_TEAM_MEMBER with ROLE='S' (Supervisor) with the request number, unit, priority and description. Never blocks the save.
# business_logic: Notify the supervisor of a Security request


def _g(h, k):
    v = h.get(k)
    return h.get(k.lower()) if v is None else v


def run(args):
    if args.get('action') != 'add':
        return None
    h = args.get('header')
    if not isinstance(h, dict):
        return None
    cat = _g(h, 'REQUEST_CATEGORY')
    no = args.get('txn_id') or _g(h, 'REQUEST_NO')
    try:
        is_sec = str(cat or '').strip().lower() == 'security'
        if not is_sec and not is_empty(cat):
            c = db.query_one('SELECT NAME FROM ' + db.t('CCW_FACILITY_REQ_CATEGORY')
                             + ' WHERE REQUEST_CATEGORY_CODE = :c', {'c': cat})
            is_sec = bool(c and str(c['NAME'] or '').strip().lower() == 'security')
        if not is_sec:
            return None
        recips = []
        for r in db.query('SELECT EMAIL FROM ' + db.t('CCW_FACILITY_TEAM_MEMBER')
                          + " WHERE ROLE = 'S' AND STATUS = 'A'"):
            if not is_empty(r['EMAIL']):
                recips.append(str(r['EMAIL']).strip())
    except Exception as ex:
        return {'warnings': [{'code': 'FRRAISE1', 'type': 'W',
                              'message': 'Request saved but supervisors could not be read: ' + str(ex)}]}
    recips = sorted(set(recips))
    if not recips:
        return {'warnings': [{'code': 'FRRAISE2', 'type': 'W',
                              'message': 'Security request saved but no active supervisor with an email was found'}]}
    prio = {'L': 'Low', 'M': 'Medium', 'H': 'High', 'U': 'Urgent'}.get(str(_g(h, 'PRIORITY') or ''), _g(h, 'PRIORITY'))
    body = ('A new Security facility request has been raised.\nRequest: ' + str(no)
            + '\nUnit: ' + str(_g(h, 'UNIT_NO') or '') + '\nPriority: ' + str(prio or '')
            + '\nDescription: ' + str(_g(h, 'DESCRIPTION') or ''))
    try:
        api.emit_event('facility_request_raised', {
            'request_no': no, 'unit_no': _g(h, 'UNIT_NO'), 'priority': prio,
            'subject': 'New Security request ' + str(no), 'message': body, 'recipients': recips})
    except Exception as ex:
        return {'warnings': [{'code': 'FRRAISE3', 'type': 'W',
                              'message': 'Request saved but the supervisor notification could not be queued: ' + str(ex)}]}
    return None
