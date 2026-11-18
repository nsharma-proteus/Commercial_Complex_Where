# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_guest_entry
# event_type: pre_commit
# function_name: prepare_guest_entry
# language: python
# description: Generate pass code/QR and notify the unit for walk-ins
# functional_specification: On action='add' only. For ENTRY_TYPE='P' (Pre-Registered): generate a random unique 6-character upper-case alphanumeric PASS_CODE (no ambiguous characters; retry until no CCW_GUEST_ENTRY row has it) and set PASS_QR to the same value (the QR payload) on the header row, STATUS='E'. For ENTRY_TYPE='W' (Walk-In): STATUS='W', EXPECTED_DATE = today, no pass code. Enforce that a Pre-Registered entry's pass is returned to the user in the success message ('Pass code: XXXXXX').
# business_logic: Generate pass code/QR and notify the unit for walk-ins

_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def _gen_code(seed):
    # deterministic-free pseudo random from clock + counter (no random module available)
    n = int(datetime.datetime.now().strftime('%H%M%S%f')) * 7919 + seed * 104729 + hash(str(seed) + str(now())) % 100003
    n = abs(n)
    out = ''
    for _ in range(6):
        out += _ALPHABET[n % len(_ALPHABET)]
        n = n // len(_ALPHABET)
        n = n * 31 + 17 + _
    return out


def _set(header, key, val):
    header[key] = val
    header[key.lower()] = val


def run(args):
    if args.get('action') != 'add':
        return None
    header = args.get('header')
    if not isinstance(header, dict):
        return 'Guest entry header is missing'
    etype = str(header.get('ENTRY_TYPE') or header.get('entry_type') or '').strip().upper()
    if etype == 'P':
        code = None
        for i in range(50):
            cand = _gen_code(i)
            hit = db.query_one('SELECT GUEST_ENTRY_NO FROM ' + db.t('CCW_GUEST_ENTRY')
                               + ' WHERE PASS_CODE = :c', {'c': cand})
            if not hit:
                code = cand
                break
        if not code:
            return 'Could not generate a unique pass code, please try again'
        _set(header, 'PASS_CODE', code)
        _set(header, 'PASS_QR', code)
        _set(header, 'STATUS', 'E')
        return {'prompts': [{'code': 'GEPASS1', 'type': 'P', 'message': 'Pass code: ' + code}]}
    if etype == 'W':
        _set(header, 'STATUS', 'W')
        _set(header, 'EXPECTED_DATE', str(today())[:10])
        return None
    return None
