# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_guest_entry
# event_type: action
# function_name: scan_guest_pass
# action_name: Scan QR Code
# language: python
# description: Look up an entry by scanned pass
# functional_specification: Normalise SCANNED_CODE (trim, upper-case, strip any wrapper such as a URL or KEY=value prefix) and find the CCW_GUEST_ENTRY with that PASS_CODE; error 'Pass not found' otherwise. Return {"message": ...} summarising GUEST_ENTRY_NO, GUEST_NAME, UNIT_NO, purpose, EXPECTED_DATE, valid window and STATUS, plus a warning when the date or time window does not match or the status is not Expected/Approved (already used or cancelled).
# business_logic: Look up an entry by scanned pass

_STATUS = {'E': 'Expected', 'W': 'Awaiting Approval', 'A': 'Approved', 'J': 'Rejected',
           'I': 'Checked In', 'O': 'Checked Out', 'C': 'Cancelled'}


def _normalise(raw):
    s = str(raw or '').strip()
    if '?' in s:
        s = s.split('?', 1)[1]
    if '=' in s:
        s = s.split('=')[-1]
    s = s.split('#')[0].rstrip('/')
    if '/' in s:
        s = s.split('/')[-1]
    return s.strip().upper()


def _hm(v):
    return str(v)[:5] if not is_empty(v) else ''


def run(args):
    code = _normalise(args.get('SCANNED_CODE'))
    if not code:
        return 'Pass not found'
    e = db.query_one('SELECT g.GUEST_ENTRY_NO, g.GUEST_NAME, g.UNIT_NO, g.PURPOSE, g.EXPECTED_DATE, '
                     'g.VALID_FROM_TIME, g.VALID_TO_TIME, g.STATUS, p.PURPOSE_NAME FROM '
                     + db.t('CCW_GUEST_ENTRY') + ' g LEFT JOIN ' + db.t('CCW_GUEST_PURPOSE_MASTER')
                     + ' p ON p.PURPOSE_CODE = g.PURPOSE WHERE g.PASS_CODE = :c', {'c': code})
    if not e:
        return 'Pass not found'
    st = e['STATUS']
    exp = str(e['EXPECTED_DATE'])[:10]
    vf, vt = _hm(e['VALID_FROM_TIME']), _hm(e['VALID_TO_TIME'])
    window = (vf + ' - ' + vt) if (vf or vt) else 'any time'
    msg = ('Entry ' + str(e['GUEST_ENTRY_NO']) + ': ' + str(e['GUEST_NAME']) + ', Unit ' + str(e['UNIT_NO'])
           + ', Purpose: ' + str(e['PURPOSE_NAME'] or e['PURPOSE']) + ', Date: ' + exp
           + ', Valid: ' + window + ', Status: ' + _STATUS.get(st, str(st)))
    warns = []
    if st not in ('E', 'A'):
        warns.append('Pass cannot be used (status ' + _STATUS.get(st, str(st)) + ')')
    if st == 'E' and exp != str(today())[:10]:
        warns.append('Expected date is ' + exp + ', not today')
    hm = str(now())[11:16] if len(str(now())) > 15 else datetime.datetime.now().strftime('%H:%M')
    if (vf and hm < vf) or (vt and hm > vt):
        warns.append('Outside valid time window ' + window)
    if warns:
        msg += ' | WARNING: ' + '; '.join(warns)
    return {'message': msg}
