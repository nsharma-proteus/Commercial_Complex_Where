# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_banner_booking
# event_type: action
# function_name: reject_booking
# action_name: Reject
# language: python
# description: Reject the booking
# functional_specification: Management only. Refuse unless BOOKING_STATUS='R'. Require a non-blank REJECTION_REASON from the payload. Set BOOKING_STATUS='J' and store REJECTION_REASON on CCW_BANNER_BOOKING; notify the advertiser (EMAIL) with the reason. Return {"message":"Booking rejected"}.
# business_logic: Reject the booking


def _is_mgmt():
    roles = [str(r).lower() for r in (api.my_roles() or [])]
    return any(r in ('management', 'admin', 'func-admin') for r in roles)


def run(args):
    if not _is_mgmt():
        return 'Only management can reject a banner booking'
    bno = args.get('BOOKING_NO')
    if is_empty(bno):
        return 'Booking number is missing'
    b = db.query_one('SELECT BOOKING_STATUS, EMAIL, ADVERTISER_NAME, BANNER_TITLE FROM '
                     + db.t('CCW_BANNER_BOOKING') + ' WHERE BOOKING_NO = :b', {'b': bno})
    if not b:
        return 'Booking not found'
    if b['BOOKING_STATUS'] != 'R':
        return 'Only a Requested booking can be rejected'
    reason = str(args.get('REJECTION_REASON') or '').strip()
    if not reason:
        return 'Rejection reason is required'
    db.update('CCW_BANNER_BOOKING', {'BOOKING_STATUS': 'J', 'REJECTION_REASON': reason[:500]},
              {'BOOKING_NO': bno})
    out = {'message': 'Booking rejected'}
    body = ('Dear ' + str(b['ADVERTISER_NAME'] or '') + ',\nYour banner booking ' + str(bno) + ' ("'
            + str(b['BANNER_TITLE'] or '') + '") has been rejected.\nReason: ' + reason)
    try:
        api.emit_event('banner_booking_rejected', {
            'booking_no': bno, 'email': b['EMAIL'], 'rejection_reason': reason,
            'subject': 'Banner booking ' + str(bno) + ' rejected', 'message': body,
            'recipients': [b['EMAIL']]})
    except Exception as ex:
        out['message'] = out['message'] + ' (' + 'Booking rejected but the notification could not be queued: ' + str(ex) + ')'
    return out
