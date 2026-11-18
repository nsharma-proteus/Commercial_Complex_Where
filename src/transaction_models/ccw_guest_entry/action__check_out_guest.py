# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_guest_entry
# event_type: action
# function_name: check_out_guest
# action_name: Check Out
# language: python
# description: Check the guest out
# functional_specification: Allowed only when STATUS='I'. Set STATUS='O' and CHECK_OUT_TIME = now (must be after CHECK_IN_TIME). Notify the unit contacts. Return {"message":"Guest checked out"}.
# business_logic: Check the guest out


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
    e = db.query_one('SELECT STATUS, CHECK_IN_TIME, UNIT_NO, GUEST_NAME FROM ' + db.t('CCW_GUEST_ENTRY')
                     + ' WHERE GUEST_ENTRY_NO = :n', {'n': no})
    if not e:
        return 'Guest entry not found'
    if e['STATUS'] != 'I':
        return 'Check Out is allowed only for Checked In entries'
    n = now()
    if not is_empty(e['CHECK_IN_TIME']) and str(n)[:19].replace('T', ' ') <= str(e['CHECK_IN_TIME'])[:19].replace('T', ' '):
        return 'Check out time must be after check in time'
    db.update('CCW_GUEST_ENTRY', {'STATUS': 'O', 'CHECK_OUT_TIME': n}, {'GUEST_ENTRY_NO': no})
    out = {'message': 'Guest checked out'}
    recips = _contacts(e['UNIT_NO'])
    if recips:
        try:
            api.emit_event('guest_checked_out', {
                'guest_entry_no': no, 'unit_no': e['UNIT_NO'], 'guest_name': e['GUEST_NAME'],
                'subject': 'Guest ' + str(e['GUEST_NAME']) + ' has left',
                'message': 'Your guest ' + str(e['GUEST_NAME']) + ' (' + str(no) + ') has checked out.',
                'recipients': recips})
        except Exception as ex:
            out['message'] += ' (notification could not be queued: ' + str(ex) + ')'
    return out
