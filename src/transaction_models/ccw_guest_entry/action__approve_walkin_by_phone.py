# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_guest_entry
# event_type: action
# function_name: approve_walkin_by_phone
# action_name: Approve by Phone
# language: python
# description: Security records a phone approval
# functional_specification: For security/management users only. Allowed only when STATUS='W'. Require a non-blank APPROVED_BY (the name of the person who approved) from the payload. Set STATUS='A', APPROVED_VIA='P' (Phone), APPROVED_BY from the payload. Return {"message":"Approval recorded by phone"}.
# business_logic: Security records a phone approval


def _is_staff():
    roles = [str(r).lower() for r in (api.my_roles() or [])]
    return any(('security' in r) or r in ('management', 'admin', 'func-admin') for r in roles)


def run(args):
    if not _is_staff():
        return 'Only security or management can record a phone approval'
    no = args.get('GUEST_ENTRY_NO')
    if is_empty(no):
        return 'Guest entry number is missing'
    e = db.query_one('SELECT STATUS FROM ' + db.t('CCW_GUEST_ENTRY') + ' WHERE GUEST_ENTRY_NO = :n', {'n': no})
    if not e:
        return 'Guest entry not found'
    if e['STATUS'] != 'W':
        return 'Only an entry Awaiting Approval can be approved'
    who = str(args.get('APPROVED_BY') or '').strip()
    if not who:
        return 'Enter the name of the person who approved by phone (Approved By)'
    db.update('CCW_GUEST_ENTRY', {'STATUS': 'A', 'APPROVED_VIA': 'P', 'APPROVED_BY': who[:100]},
              {'GUEST_ENTRY_NO': no})
    return {'message': 'Approval recorded by phone'}
