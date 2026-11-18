# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_guest_entry
# event_type: action
# function_name: check_in_guest
# action_name: Check In
# language: python
# description: Check the guest in
# functional_specification: Allowed only when STATUS is 'E' (Expected, and EXPECTED_DATE = today) or 'A' (Approved); an Expected entry on a different date, or an entry checked in outside VALID_FROM_TIME..VALID_TO_TIME (when set), requires a non-blank SECURITY_REMARK from the payload, else error. Set STATUS='I', CHECK_IN_TIME = now, CHECKED_IN_BY = signed-in user's email, SECURITY_REMARK from the payload when given. Notify the unit contacts (unit owners from CCW_MEMBER_OWNER and the active tenant). Return {"message":"Guest checked in"}.
# business_logic: Check the guest in


def _me(args):
    for k in ('user_email', 'USER_EMAIL', '_user_email'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip()
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('email')):
        return str(u.get('email')).strip()
    return None


def _contacts(unit):
    out = []
    for r in db.query('SELECT OWNER_EMAIL FROM ' + db.t('CCW_MEMBER_OWNER') + ' WHERE UNIT_NO = :u', {'u': unit}):
        if not is_empty(r['OWNER_EMAIL']):
            out.append(str(r['OWNER_EMAIL']).strip())
    t = db.query_one('SELECT TENANT_EMAIL FROM ' + db.t('CCW_TENANT_PROFILE')
                     + " WHERE UNIT_NO = :u AND TENANT_STATUS = 'A'", {'u': unit})
    if t and not is_empty(t['TENANT_EMAIL']):
        out.append(str(t['TENANT_EMAIL']).strip())
    return sorted(set(out))


def run(args):
    no = args.get('GUEST_ENTRY_NO')
    if is_empty(no):
        return 'Guest entry number is missing'
    e = db.query_one('SELECT * FROM ' + db.t('CCW_GUEST_ENTRY') + ' WHERE GUEST_ENTRY_NO = :n', {'n': no})
    if not e:
        return 'Guest entry not found'
    st = e['STATUS']
    if st not in ('E', 'A'):
        return 'Check In is allowed only for Expected or Approved entries'
    remark = str(args.get('SECURITY_REMARK') or '').strip()
    if not remark:
        remark = str(e['SECURITY_REMARK'] or '').strip()
    reasons = []
    today_s = str(today())[:10]
    if st == 'E' and str(e['EXPECTED_DATE'])[:10] != today_s:
        reasons.append('checked in on a different date than expected')
    hm = datetime.datetime.now().strftime('%H:%M')
    vf = str(e['VALID_FROM_TIME'])[:5] if not is_empty(e['VALID_FROM_TIME']) else ''
    vt = str(e['VALID_TO_TIME'])[:5] if not is_empty(e['VALID_TO_TIME']) else ''
    if (vf and hm < vf) or (vt and hm > vt):
        reasons.append('checked in outside the valid time window')
    if reasons and not remark:
        return 'A Security Remark is required: guest is ' + ' and '.join(reasons)
    me = _me(args)
    upd = {'STATUS': 'I', 'CHECK_IN_TIME': now(), 'CHECKED_IN_BY': me}
    if remark:
        upd['SECURITY_REMARK'] = remark[:500]
    db.update('CCW_GUEST_ENTRY', upd, {'GUEST_ENTRY_NO': no})
    out = {'message': 'Guest checked in'}
    recips = _contacts(e['UNIT_NO'])
    if recips:
        try:
            api.emit_event('guest_checked_in', {
                'guest_entry_no': no, 'unit_no': e['UNIT_NO'], 'guest_name': e['GUEST_NAME'],
                'subject': 'Guest ' + str(e['GUEST_NAME']) + ' has arrived',
                'message': 'Your guest ' + str(e['GUEST_NAME']) + ' (' + str(no) + ') has checked in.',
                'recipients': recips})
        except Exception as ex:
            out['message'] += ' (notification could not be queued: ' + str(ex) + ')'
    return out
