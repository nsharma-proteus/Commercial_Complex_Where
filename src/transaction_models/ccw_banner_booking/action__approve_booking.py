# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_banner_booking
# event_type: action
# function_name: approve_booking
# action_name: Approve
# language: python
# description: Approve the booking, check capacity and generate the invoice
# functional_specification: Management only. Refuse unless BOOKING_STATUS='R'. Compute the period: START_DATE to END_DATE = START_DATE + NO_OF_MONTHS months - 1 day. Read MAX_CAROUSEL_SLOTS from the Active plan in CCW_BANNER_RATE_PLAN_MASTER (STATUS='A'; error if none). For every day D of the period count CCW_BANNER_BOOKING rows with BOOKING_STATUS='A' whose own period (start_date to start_date + no_of_months months - 1 day) covers D; the booked count must stay below MAX_CAROUSEL_SLOTS on every day (i.e. existing approved count + this booking <= MAX_CAROUSEL_SLOTS). If any day is full, block approval with an error stating the next available start date: the first date on/after START_DATE from which a period of NO_OF_MONTHS months has fewer approved bookings than MAX_CAROUSEL_SLOTS on every day. On success set BOOKING_STATUS='A', generate a unique INVOICE_NO (e.g. 'BNR/' + financial year + '/' + zero-padded running serial) and INVOICE_DATE = today, then email the advertiser (EMAIL) the invoice details (invoice no, date, period, amount, tax, total). Return {"message":"Booking approved; invoice <INVOICE_NO> raised"}.
# business_logic: Approve the booking, check capacity and generate the invoice


def _is_mgmt():
    roles = [str(r).lower() for r in (api.my_roles() or [])]
    return any(r in ('management', 'admin', 'func-admin') for r in roles)


def _d(v):
    if v is None or v == '':
        return None
    return to_date(str(v)[:10])


def _add_months(d, n):
    m0 = d.month - 1 + int(n)
    y = d.year + m0 // 12
    m = m0 % 12 + 1
    nxt = datetime.date(y + (1 if m == 12 else 0), 1 if m == 12 else m + 1, 1)
    last = (nxt - timedelta(days=1)).day
    return datetime.date(y, m, min(d.day, last))


def _end(start, n):
    return _add_months(start, n) - timedelta(days=1)


def _fy(d):
    y = d.year if d.month >= 4 else d.year - 1
    return '%d-%02d' % (y, (y + 1) % 100)


def run(args):
    if not _is_mgmt():
        return 'Only management can approve a banner booking'
    bno = args.get('BOOKING_NO')
    if is_empty(bno):
        return 'Booking number is missing'
    b = db.query_one('SELECT * FROM ' + db.t('CCW_BANNER_BOOKING') + ' WHERE BOOKING_NO = :b', {'b': bno})
    if not b:
        return 'Booking not found'
    if b['BOOKING_STATUS'] != 'R':
        return 'Only a Requested booking can be approved'
    start = _d(b['START_DATE'])
    months = int(to_number(b['NO_OF_MONTHS']) or 0)
    if start is None or months < 1:
        return 'Booking needs a start date and number of months before approval'
    end = _end(start, months)

    plan = db.query_one('SELECT MAX_CAROUSEL_SLOTS FROM ' + db.t('CCW_BANNER_RATE_PLAN_MASTER')
                        + " WHERE STATUS = 'A'", {})
    if not plan:
        return 'No Active Banner Rate Plan found; cannot check carousel capacity'
    slots = int(to_number(plan['MAX_CAROUSEL_SLOTS']) or 0)

    rows = db.query('SELECT START_DATE, NO_OF_MONTHS FROM ' + db.t('CCW_BANNER_BOOKING')
                    + " WHERE BOOKING_STATUS = 'A' AND BOOKING_NO <> :b AND START_DATE <= :e",
                    {'b': bno, 'e': end})
    # approved periods; the filter above is an upper bound only for the requested period,
    # next-available search may need later ones, so fetch all later approved too
    later = db.query('SELECT START_DATE, NO_OF_MONTHS FROM ' + db.t('CCW_BANNER_BOOKING')
                     + " WHERE BOOKING_STATUS = 'A' AND BOOKING_NO <> :b AND START_DATE > :e",
                     {'b': bno, 'e': end})
    periods = []
    for r in list(rows) + list(later):
        s = _d(r['START_DATE'])
        n = int(to_number(r['NO_OF_MONTHS']) or 0)
        if s is None or n < 1:
            continue
        periods.append((s, _end(s, n)))
    periods = [p for p in periods if p[1] >= start]

    counts = {}
    horizon = start
    for s, e in periods:
        d = s if s > start else start
        if e > horizon:
            horizon = e
        while d <= e:
            counts[d] = counts.get(d, 0) + 1
            d = d + timedelta(days=1)

    def fits(c):
        ce = _end(c, months)
        d = c
        while d <= ce and d <= horizon:
            if counts.get(d, 0) >= slots:
                return False
            d = d + timedelta(days=1)
        return True

    if not fits(start):
        cands = [start] + sorted(set(e + timedelta(days=1) for s, e in periods if e + timedelta(days=1) > start))
        nxt = None
        for c in cands:
            if fits(c):
                nxt = c
                break
        if nxt is None:
            nxt = horizon + timedelta(days=1)
        return ('Carousel is full for ' + str(start) + ' to ' + str(end) + '. Next available start date: '
                + str(nxt))

    today_d = today()
    prefix = 'BNR/' + _fy(today_d) + '/'
    existing = db.query('SELECT INVOICE_NO FROM ' + db.t('CCW_BANNER_BOOKING')
                        + ' WHERE INVOICE_NO LIKE :p', {'p': prefix + '%'})
    serial = 0
    for r in existing:
        tail = str(r['INVOICE_NO'] or '')[len(prefix):]
        if tail.isdigit() and int(tail) > serial:
            serial = int(tail)
    inv = prefix + str(serial + 1).zfill(5)

    db.update('CCW_BANNER_BOOKING',
              {'BOOKING_STATUS': 'A', 'INVOICE_NO': inv, 'INVOICE_DATE': today_d},
              {'BOOKING_NO': bno})

    out = {'message': 'Booking approved; invoice ' + inv + ' raised'}
    body = ('Dear ' + str(b['ADVERTISER_NAME'] or '') + ',\nYour banner booking ' + str(bno) + ' ("'
            + str(b['BANNER_TITLE'] or '') + '") is approved.\nInvoice no: ' + inv + '\nInvoice date: '
            + str(today_d) + '\nPeriod: ' + str(start) + ' to ' + str(end) + '\nAmount: ' + str(b['AMOUNT'])
            + '\nTax: ' + str(b['TAX_AMOUNT']) + '\nTotal: ' + str(b['TOTAL_AMOUNT']))
    try:
        api.emit_event('banner_booking_approved', {
            'booking_no': bno, 'email': b['EMAIL'], 'invoice_no': inv, 'invoice_date': str(today_d),
            'start_date': str(start), 'end_date': str(end), 'amount': str(b['AMOUNT']),
            'tax_amount': str(b['TAX_AMOUNT']), 'total_amount': str(b['TOTAL_AMOUNT']),
            'subject': 'Banner booking ' + str(bno) + ' approved - invoice ' + inv, 'message': body,
            'recipients': [b['EMAIL']]})
    except Exception as ex:
        out['message'] = out['message'] + ' (' + 'Booking approved but the invoice email could not be queued: ' + str(ex) + ')'
    return out
