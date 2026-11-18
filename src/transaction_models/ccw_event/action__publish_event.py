# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_event
# event_type: action
# function_name: publish_event
# action_name: Publish
# language: python
# description: Publish the event and notify the audience
# functional_specification: For the given EVENT_NO in CCW_EVENT: refuse with an error unless STATUS='D'; refuse with an error if START_DATE_TIME is earlier than the current date-time ('Start date/time cannot be in the past when publishing'). Set STATUS='P'. Then create an in-app notification and send an email to the intended audience: owners (CCW_MEMBER_OWNER.OWNER_EMAIL joined to CCW_MEMBER_PROFILE on UNIT_NO where PROFILE_STATUS='A' and LOGIN_ENABLED='Y') plus, unless AUDIENCE='O', active tenants with login (CCW_TENANT_PROFILE.TENANT_EMAIL where TENANT_STATUS='A' and LOGIN_ENABLED='Y'). When AUDIENCE='W' restrict to units (CCW_UNIT_MASTER) whose WING_CODE equals the event WING_CODE. Message includes title, venue, start and end. Return {"message":"Event published"}.
# business_logic: Publish the event and notify the audience


def _audience_emails(audience, wing):
    emails = []
    wing_join = ''
    params = {}
    if audience == 'W':
        wing_join = ' JOIN ' + db.t('CCW_UNIT_MASTER') + ' u ON u.UNIT_NO = p.UNIT_NO AND u.WING_CODE = :wing'
        params['wing'] = wing
    sql = ('SELECT o.OWNER_EMAIL AS EMAIL FROM ' + db.t('CCW_MEMBER_OWNER') + ' o JOIN '
           + db.t('CCW_MEMBER_PROFILE') + ' p ON p.UNIT_NO = o.UNIT_NO' + wing_join
           + " WHERE p.PROFILE_STATUS = 'A' AND o.LOGIN_ENABLED = 'Y'")
    for r in db.query(sql, params):
        emails.append(r['EMAIL'])
    if audience != 'O':
        wing_join_t = ''
        if audience == 'W':
            wing_join_t = ' JOIN ' + db.t('CCW_UNIT_MASTER') + ' u ON u.UNIT_NO = t.UNIT_NO AND u.WING_CODE = :wing'
        sql = ('SELECT t.TENANT_EMAIL AS EMAIL FROM ' + db.t('CCW_TENANT_PROFILE') + ' t' + wing_join_t
               + " WHERE t.TENANT_STATUS = 'A' AND t.LOGIN_ENABLED = 'Y'")
        for r in db.query(sql, params):
            emails.append(r['EMAIL'])
    seen = set()
    out = []
    for e in emails:
        e = (e or '').strip()
        if e and e.lower() not in seen:
            seen.add(e.lower())
            out.append(e)
    return out


def run(args):
    event_no = args.get('EVENT_NO')
    if is_empty(event_no):
        return 'Event number is required'
    ev = db.query_one('SELECT * FROM ' + db.t('CCW_EVENT') + ' WHERE EVENT_NO = :n', {'n': event_no})
    if not ev:
        return 'Event not found'
    if ev['STATUS'] != 'D':
        return 'Only a Draft event can be published'
    start = ev['START_DATE_TIME']
    start_s = str(start)[:19].replace('T', ' ')
    now_s = now().strftime('%Y-%m-%d %H:%M:%S')
    if start_s < now_s:
        return 'Start date/time cannot be in the past when publishing'

    db.update('CCW_EVENT', {'STATUS': 'P'}, {'EVENT_NO': event_no})

    audience = ev['AUDIENCE']
    wing = ev['WING_CODE']
    if audience == 'W' and is_empty(wing):
        return {'message': 'Event published',
                'warnings': [{'code': 'EVNOWING', 'type': 'W', 'message': 'No wing set for a wing-specific event; no one was notified'}]}
    emails = _audience_emails(audience, wing)
    subject = 'Event: ' + str(ev['TITLE'])
    body = ('Event: ' + str(ev['TITLE']) + '\nVenue: ' + str(ev['VENUE'])
            + '\nStart: ' + start_s + '\nEnd: ' + str(ev['END_DATE_TIME'])[:19].replace('T', ' '))
    if emails:
        try:
            api.emit_event('event_published', {
                'event_no': event_no, 'title': ev['TITLE'], 'venue': ev['VENUE'],
                'start_date_time': start_s, 'end_date_time': str(ev['END_DATE_TIME'])[:19],
                'subject': subject, 'message': body, 'recipients': emails})
        except Exception as e:
            return {'message': 'Event published',
                    'warnings': [{'code': 'EVNOTIFY', 'type': 'W', 'message': 'Event published but notification failed: ' + str(e)}]}
    return {'message': 'Event published'}
