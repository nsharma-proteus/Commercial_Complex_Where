# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_banner_booking
# event_type: action
# function_name: cancel_booking
# action_name: Cancel
# language: python
# description: Cancel the booking before its start date
# functional_specification: Allowed for the booking's owner (ADD_USER) or management. Refuse unless BOOKING_STATUS is 'R' or 'A' and START_DATE is after today ('Cancel is allowed before the start date'). Set BOOKING_STATUS='C'. Refunds are settled outside the system; if PAYMENT_STATUS='P' include that note in the returned message. Return {"message":"Booking cancelled"}.
# business_logic: Cancel the booking before its start date


def _is_mgmt():
    roles = [str(r).lower() for r in (api.my_roles() or [])]
    return any(r in ('management', 'admin', 'func-admin') for r in roles)


def _me_short(args):
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('user_id')):
        return str(u.get('user_id')).strip()[:10]
    for k in ('short_user_id', 'SHORT_USER_ID', 'user_id', 'USER_ID'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip()[:10]
    return None


def run(args):
    bno = args.get('BOOKING_NO')
    if is_empty(bno):
        return 'Booking number is missing'
    b = db.query_one('SELECT BOOKING_STATUS, PAYMENT_STATUS, START_DATE, ADD_USER FROM '
                     + db.t('CCW_BANNER_BOOKING') + ' WHERE BOOKING_NO = :b', {'b': bno})
    if not b:
        return 'Booking not found'
    owner = str(b['ADD_USER'] or '').strip()
    me = _me_short(args)
    # when no identity is supplied, row security has already limited access to the record
    if me is not None and me != owner and not _is_mgmt():
        return 'Only the booking owner or management can cancel this booking'
    if b['BOOKING_STATUS'] not in ('R', 'A'):
        return 'Only a Requested or Approved booking can be cancelled'
    start = to_date(str(b['START_DATE'])[:10]) if not is_empty(b['START_DATE']) else None
    if start is None or not (start > today()):
        return 'Cancel is allowed before the start date'
    db.update('CCW_BANNER_BOOKING', {'BOOKING_STATUS': 'C'}, {'BOOKING_NO': bno})
    msg = 'Booking cancelled'
    if b['PAYMENT_STATUS'] == 'P':
        msg += '. Refunds are settled outside the system.'
    return {'message': msg}
