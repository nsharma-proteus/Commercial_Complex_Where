# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_guest_entry
# event_type: action
# function_name: cancel_guest_entry
# action_name: Cancel
# language: python
# description: Cancel the entry
# functional_specification: Allowed for the registering user, residents of the unit, or security/management, when STATUS is 'E', 'W' or 'A'. Set STATUS='C'; the record is then locked. Return {"message":"Entry cancelled"}.
# business_logic: Cancel the entry


def _me(args):
    for k in ('user_email', 'USER_EMAIL', '_user_email'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip()
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('email')):
        return str(u.get('email')).strip()
    return None


def _is_staff():
    roles = [str(r).lower() for r in (api.my_roles() or [])]
    return any(('security' in r) or r in ('management', 'admin', 'func-admin') for r in roles)


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
    e = db.query_one('SELECT STATUS, UNIT_NO, REGISTERED_BY FROM ' + db.t('CCW_GUEST_ENTRY')
                     + ' WHERE GUEST_ENTRY_NO = :n', {'n': no})
    if not e:
        return 'Guest entry not found'
    if e['STATUS'] not in ('E', 'W', 'A'):
        return 'Only Expected, Awaiting Approval or Approved entries can be cancelled'
    me = _me(args)
    own = bool(me and str(e['REGISTERED_BY'] or '').strip().lower() == me.lower())
    if not (own or _is_staff() or _is_resident(e['UNIT_NO'], me)):
        return 'Only the registering user, a resident of the unit, security or management can cancel this entry'
    db.update('CCW_GUEST_ENTRY', {'STATUS': 'C'}, {'GUEST_ENTRY_NO': no})
    return {'message': 'Entry cancelled'}
