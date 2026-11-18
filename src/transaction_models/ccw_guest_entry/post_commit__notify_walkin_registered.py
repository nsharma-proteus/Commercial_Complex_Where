# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_guest_entry
# event_type: post_commit
# function_name: notify_walkin_registered
# language: python
# description: Ask the unit to approve a Walk-In
# functional_specification: On action='add' with ENTRY_TYPE='W': create an in-app notification and email to every owner of the entry's UNIT_NO (CCW_MEMBER_OWNER.OWNER_EMAIL with LOGIN_ENABLED='Y') and to the active tenant with login (CCW_TENANT_PROFILE, TENANT_STATUS='A', LOGIN_ENABLED='Y') asking them to Approve or Reject the guest (name, company, purpose, persons). Never blocks the save.
# business_logic: Ask the unit to approve a Walk-In


def _g(h, k):
    v = h.get(k)
    return h.get(k.lower()) if v is None else v


def run(args):
    if args.get('action') != 'add':
        return None
    h = args.get('header')
    if not isinstance(h, dict) or str(_g(h, 'ENTRY_TYPE') or '').upper() != 'W':
        return None
    unit = _g(h, 'UNIT_NO')
    no = args.get('txn_id') or _g(h, 'GUEST_ENTRY_NO')
    recips = []
    try:
        for r in db.query('SELECT OWNER_EMAIL FROM ' + db.t('CCW_MEMBER_OWNER')
                          + " WHERE UNIT_NO = :u AND LOGIN_ENABLED = 'Y'", {'u': unit}):
            if not is_empty(r['OWNER_EMAIL']):
                recips.append(str(r['OWNER_EMAIL']).strip())
        t = db.query_one('SELECT TENANT_EMAIL FROM ' + db.t('CCW_TENANT_PROFILE')
                         + " WHERE UNIT_NO = :u AND TENANT_STATUS = 'A' AND LOGIN_ENABLED = 'Y'", {'u': unit})
        if t and not is_empty(t['TENANT_EMAIL']):
            recips.append(str(t['TENANT_EMAIL']).strip())
    except Exception as ex:
        return {'warnings': [{'code': 'GEWI1', 'type': 'W',
                              'message': 'Walk-In saved but unit contacts could not be read: ' + str(ex)}]}
    recips = sorted(set(recips))
    if not recips:
        return {'warnings': [{'code': 'GEWI2', 'type': 'W',
                              'message': 'Walk-In saved but no unit contact with login was found to notify'}]}
    body = ('A walk-in guest is waiting for approval.\nGuest: ' + str(_g(h, 'GUEST_NAME') or '')
            + '\nCompany: ' + str(_g(h, 'GUEST_COMPANY') or '-')
            + '\nPurpose: ' + str(_g(h, 'PURPOSE') or '')
            + '\nPersons: ' + str(_g(h, 'NO_OF_PERSONS') or '')
            + '\nPlease Approve or Reject entry ' + str(no) + '.')
    try:
        api.emit_event('guest_walkin_approval_requested', {
            'guest_entry_no': no, 'unit_no': unit, 'guest_name': _g(h, 'GUEST_NAME'),
            'subject': 'Walk-In guest awaiting your approval (' + str(no) + ')',
            'message': body, 'recipients': recips})
    except Exception as ex:
        return {'warnings': [{'code': 'GEWI3', 'type': 'W',
                              'message': 'Walk-In saved but the approval request could not be queued: ' + str(ex)}]}
    return None
