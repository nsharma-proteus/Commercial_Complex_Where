# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_banner_booking
# event_type: action
# function_name: record_booking_payment
# action_name: Record Payment
# language: python
# description: Record payment and make the banner eligible for the carousel
# functional_specification: Management only. Refuse unless BOOKING_STATUS='A' and PAYMENT_STATUS='U' ('A booking can be recorded as Paid only after Approval'). Require PAYMENT_MODE, PAYMENT_REFERENCE and PAYMENT_DATE (not in the future) on the saved record; default RECEIVED_BY to the signed-in user's email when blank. Set PAYMENT_STATUS='P' on CCW_BANNER_BOOKING. The banner is then eligible for the carousel (Live when today is within START_DATE..END_DATE). Notify the advertiser (EMAIL) that payment was received. Return {"message":"Payment recorded"}.
# business_logic: Record payment and make the banner eligible for the carousel


def _is_mgmt():
    roles = [str(r).lower() for r in (api.my_roles() or [])]
    return any(r in ('management', 'admin', 'func-admin') for r in roles)


def _me(args):
    for k in ('user_email', 'USER_EMAIL', '_user_email'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip()
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('email')):
        return str(u.get('email')).strip()
    return None


def run(args):
    if not _is_mgmt():
        return 'Only management can record a payment'
    bno = args.get('BOOKING_NO')
    if is_empty(bno):
        return 'Booking number is missing'
    b = db.query_one('SELECT * FROM ' + db.t('CCW_BANNER_BOOKING') + ' WHERE BOOKING_NO = :b', {'b': bno})
    if not b:
        return 'Booking not found'
    if b['BOOKING_STATUS'] != 'A' or b['PAYMENT_STATUS'] != 'U':
        return 'A booking can be recorded as Paid only after Approval (and only once)'

    mode = args.get('PAYMENT_MODE') if not is_empty(args.get('PAYMENT_MODE')) else b['PAYMENT_MODE']
    ref = args.get('PAYMENT_REFERENCE') if not is_empty(args.get('PAYMENT_REFERENCE')) else b['PAYMENT_REFERENCE']
    pdate = args.get('PAYMENT_DATE') if not is_empty(args.get('PAYMENT_DATE')) else b['PAYMENT_DATE']
    recv = args.get('RECEIVED_BY') if not is_empty(args.get('RECEIVED_BY')) else b['RECEIVED_BY']
    errs = []
    if is_empty(mode):
        errs.append('Payment mode is required')
    if is_empty(ref) or not str(ref).strip():
        errs.append('Payment reference is required')
    pd = None
    if is_empty(pdate):
        errs.append('Payment date is required')
    else:
        pd = to_date(str(pdate)[:10])
        if pd > today():
            errs.append('Payment date cannot be in the future')
    if errs:
        return {'error': errs[0], 'errors': [{'code': 'BNR_PAY' + str(i + 1), 'type': 'E', 'message': m}
                                             for i, m in enumerate(errs)]}
    if is_empty(recv):
        recv = _me(args) or b['RECEIVED_BY']

    db.update('CCW_BANNER_BOOKING',
              {'PAYMENT_STATUS': 'P', 'PAYMENT_MODE': mode, 'PAYMENT_REFERENCE': str(ref).strip(),
               'PAYMENT_DATE': pd, 'RECEIVED_BY': recv},
              {'BOOKING_NO': bno})
    out = {'message': 'Payment recorded'}
    body = ('Dear ' + str(b['ADVERTISER_NAME'] or '') + ',\nWe have received your payment for banner booking '
            + str(bno) + ' (invoice ' + str(b['INVOICE_NO'] or '') + ').\nAmount: ' + str(b['TOTAL_AMOUNT'])
            + '\nPayment date: ' + str(pd) + '\nReference: ' + str(ref).strip())
    try:
        api.emit_event('banner_payment_received', {
            'booking_no': bno, 'email': b['EMAIL'], 'invoice_no': b['INVOICE_NO'],
            'total_amount': str(b['TOTAL_AMOUNT']), 'payment_date': str(pd), 'payment_reference': str(ref).strip(),
            'subject': 'Payment received for banner booking ' + str(bno), 'message': body,
            'recipients': [b['EMAIL']]})
    except Exception as ex:
        out['message'] = out['message'] + ' (' + 'Payment recorded but the notification could not be queued: ' + str(ex) + ')'
    return out
