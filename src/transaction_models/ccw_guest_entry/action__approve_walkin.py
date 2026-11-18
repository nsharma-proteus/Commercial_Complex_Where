# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_guest_entry
# event_type: action
# function_name: approve_walkin
# action_name: Approve
# language: python
# description: Resident approves a Walk-In guest
# functional_specification: Allowed only when STATUS='W' (Awaiting Approval). The signed-in user's email must match CCW_MEMBER_OWNER.OWNER_EMAIL for the entry's UNIT_NO, or CCW_TENANT_PROFILE.TENANT_EMAIL for that unit with TENANT_STATUS='A' (case-insensitive); otherwise error 'Only a member or active tenant of this unit can approve'. Set STATUS='A', APPROVED_VIA='A' (App), APPROVED_BY = the user's name/email. Notify the security desk / unit contacts. Return {"message":"Guest approved"}.
# business_logic: Resident approves a Walk-In guest


def _me(args):
    for k in ('user_email', 'USER_EMAIL', '_user_email'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip()
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('email')):
        return str(u.get('email')).strip()
    return None


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
    e = db.query_one('SELECT STATUS, UNIT_NO, GUEST_NAME FROM ' + db.t('CCW_GUEST_ENTRY')
                     + ' WHERE GUEST_ENTRY_NO = :n', {'n': no})
    if not e:
        return 'Guest entry not found'
    if e['STATUS'] != 'W':
        return 'Only an entry Awaiting Approval can be approved'
    me = _me(args)
    if not _is_resident(e['UNIT_NO'], me):
        return 'Only a member or active tenant of this unit can approve'
    db.update('CCW_GUEST_ENTRY', {'STATUS': 'A', 'APPROVED_VIA': 'A', 'APPROVED_BY': me},
              {'GUEST_ENTRY_NO': no})
    out = {'message': 'Guest approved'}
    recips = _contacts(e['UNIT_NO'])
    if recips:
        try:
            api.emit_event('guest_walkin_approved', {
                'guest_entry_no': no, 'unit_no': e['UNIT_NO'], 'guest_name': e['GUEST_NAME'],
                'subject': 'Walk-In guest ' + str(e['GUEST_NAME']) + ' approved',
                'message': 'Walk-in guest ' + str(e['GUEST_NAME']) + ' (' + str(no) + ') was approved by ' + str(me) + '.',
                'recipients': recips})
        except Exception as ex:
            out['message'] += ' (notification could not be queued: ' + str(ex) + ')'
    return out
