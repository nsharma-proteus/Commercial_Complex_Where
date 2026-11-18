# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_banner_booking
# event_type: form_validation
# function_name: validate_booking_edit
# form_no: 1
# language: python
# description: Post-approval edit guard
# functional_specification: Only when _action = 'edit': read the stored CCW_BANNER_BOOKING row for BOOKING_NO. If stored BOOKING_STATUS <> 'R', return an error when any of ADVERTISER_TYPE, UNIT_NO, ADVERTISER_NAME, CONTACT_NO, EMAIL, BANNER_TITLE, BANNER_IMAGE, CLICK_URL, START_DATE, NO_OF_MONTHS, RATE_PER_MONTH, AMOUNT, TAX_PCT, TAX_AMOUNT, TOTAL_AMOUNT differs from the stored value ('After approval only the payment fields can be edited'). If stored BOOKING_STATUS is not 'A' or PAYMENT_STATUS = 'P', also refuse changes to PAYMENT_MODE, PAYMENT_REFERENCE, PAYMENT_DATE, RECEIVED_BY. Also refuse any change to BOOKING_STATUS, PAYMENT_STATUS, INVOICE_NO, INVOICE_DATE, REJECTION_REASON through the form (they change only through actions). Return None when valid.
# business_logic: Post-approval edit guard

_NUM = ('NO_OF_MONTHS', 'RATE_PER_MONTH', 'AMOUNT', 'TAX_PCT', 'TAX_AMOUNT', 'TOTAL_AMOUNT')
_DATE = ('START_DATE', 'PAYMENT_DATE', 'INVOICE_DATE')


def _norm(col, v):
    if v is None:
        return ''
    s = str(v).strip()
    if s == '':
        return ''
    if col in _NUM:
        try:
            return str(Decimal(s).normalize())
        except Exception:
            return s
    if col in _DATE:
        return s[:10]
    return s


def _changed(args, st, cols):
    return [c for c in cols if _norm(c, args.get(c)) != _norm(c, st.get(c))]


def run(args):
    if args.get('_action') != 'edit':
        return None
    bno = args.get('BOOKING_NO')
    if is_empty(bno):
        return None
    st = db.query_one('SELECT * FROM ' + db.t('CCW_BANNER_BOOKING') + ' WHERE BOOKING_NO = :b', {'b': bno})
    if not st:
        return None
    errs = []
    if st['BOOKING_STATUS'] != 'R':
        locked = ['ADVERTISER_TYPE', 'UNIT_NO', 'ADVERTISER_NAME', 'CONTACT_NO', 'EMAIL',
                  'BANNER_TITLE', 'CLICK_URL', 'START_DATE', 'NO_OF_MONTHS',
                  'RATE_PER_MONTH', 'AMOUNT', 'TAX_PCT', 'TAX_AMOUNT', 'TOTAL_AMOUNT']
        if st['BOOKING_STATUS'] != 'A':
            locked.append('BANNER_IMAGE')  # the image may be replaced on an Approved booking
        bad = _changed(args, st, tuple(locked))
        if bad:
            errs.append('After approval only the payment fields can be edited (changed: '
                        + ', '.join(bad) + ')')
    if st['BOOKING_STATUS'] != 'A' or st['PAYMENT_STATUS'] == 'P':
        bad = _changed(args, st, ('PAYMENT_MODE', 'PAYMENT_REFERENCE', 'PAYMENT_DATE', 'RECEIVED_BY'))
        if bad:
            errs.append('Payment details can be edited only on an Approved, unpaid booking (changed: '
                        + ', '.join(bad) + ')')
    bad = _changed(args, st, ('BOOKING_STATUS', 'PAYMENT_STATUS', 'INVOICE_NO', 'INVOICE_DATE',
                              'REJECTION_REASON'))
    if bad:
        errs.append('These fields change only through actions, not the form: ' + ', '.join(bad))
    if not errs:
        return None
    return {'error': errs[0], 'errors': [{'code': 'BNR_EDIT' + str(i + 1), 'type': 'E', 'message': m}
                                         for i, m in enumerate(errs)]}
