# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_guest_entry
# event_type: action
# function_name: reject_walkin
# action_name: Reject
# language: python
# description: Resident rejects a Walk-In guest
# functional_specification: Allowed only when STATUS='W' and only for a member (CCW_MEMBER_OWNER.OWNER_EMAIL) or active tenant (CCW_TENANT_PROFILE.TENANT_EMAIL, TENANT_STATUS='A') of the entry's UNIT_NO, matched to the signed-in user's email (case-insensitive). Set STATUS='J' (Rejected), APPROVED_VIA='A', APPROVED_BY = the user. The record is then locked. Return {"message":"Guest rejected"}.
# business_logic: Resident rejects a Walk-In guest


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


def run(args):
    no = args.get('GUEST_ENTRY_NO')
    if is_empty(no):
        return 'Guest entry number is missing'
    e = db.query_one('SELECT STATUS, UNIT_NO FROM ' + db.t('CCW_GUEST_ENTRY')
                     + ' WHERE GUEST_ENTRY_NO = :n', {'n': no})
    if not e:
        return 'Guest entry not found'
    if e['STATUS'] != 'W':
        return 'Only an entry Awaiting Approval can be rejected'
    me = _me(args)
    if not _is_resident(e['UNIT_NO'], me):
        return 'Only a member or active tenant of this unit can reject'
    db.update('CCW_GUEST_ENTRY', {'STATUS': 'J', 'APPROVED_VIA': 'A', 'APPROVED_BY': me},
              {'GUEST_ENTRY_NO': no})
    return {'message': 'Guest rejected'}
