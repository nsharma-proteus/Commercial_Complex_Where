# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_business_query
# event_type: post_commit
# function_name: notify_query_recipients
# language: python
# description: Email and notify recipients on first save
# functional_specification: Run only when action = 'add'. For every CCW_BQ_RECIPIENT row of the saved QUERY_NO, create an in-app notification and send an email containing SUBJECT, DESCRIPTION and the raiser's contact details (RAISED_BY_NAME, RAISED_BY_UNIT_NO, RAISED_BY_EMAIL, and the raiser's CCW_MEMBER_PROFILE.CONTACT_NO_1). Failures must not affect the save.
# business_logic: Email and notify recipients on first save


def _h(header, key):
    v = header.get(key)
    if v is None:
        v = header.get(key.lower())
    return v


def run(args):
    if args.get('action') != 'add':
        return None
    header = args.get('header') or {}
    query_no = _h(header, 'QUERY_NO')
    if is_empty(query_no):
        return None

    recips = db.query(
        'SELECT UNIT_NO, BUSINESS_NAME, RECIPIENT_EMAIL FROM ' + db.t('CCW_BQ_RECIPIENT')
        + ' WHERE QUERY_NO = :q ORDER BY LINE_NO', {'q': query_no})
    if not recips:
        return None

    raiser_unit = _h(header, 'RAISED_BY_UNIT_NO')
    raiser_contact = None
    if not is_empty(raiser_unit):
        prof = db.get('CCW_MEMBER_PROFILE', {'UNIT_NO': raiser_unit})
        if prof:
            raiser_contact = prof['CONTACT_NO_1']

    failures = 0
    last_err = None
    for r in recips:
        try:
            api.emit_event('business_query_forwarded', {
                'query_no': query_no,
                'subject': _h(header, 'SUBJECT'),
                'description': _h(header, 'DESCRIPTION'),
                'recipient_email': r['RECIPIENT_EMAIL'],
                'recipient_unit_no': r['UNIT_NO'],
                'recipient_business_name': r['BUSINESS_NAME'],
                'raised_by_name': _h(header, 'RAISED_BY_NAME'),
                'raised_by_unit_no': raiser_unit,
                'raised_by_email': _h(header, 'RAISED_BY_EMAIL'),
                'raised_by_contact_no': raiser_contact,
            })
        except Exception as e:
            if 'not defined' in str(e):
                # No Integration Design event wired yet: delivery is skipped, the save stands.
                return None
            failures += 1
            last_err = str(e)

    if failures:
        return {'warnings': [{
            'code': 'BQ_NOTIFY_FAIL', 'type': 'W',
            'message': 'Query saved but %d recipient notification(s) could not be sent: %s' % (failures, last_err)}]}
    return None
