# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_event
# event_type: action
# function_name: cancel_event
# action_name: Cancel
# language: python
# description: Cancel the event and notify the audience
# functional_specification: Read the captured CANCELLATION_REASON from the payload; return an error 'Cancellation reason is required' if blank. For the given EVENT_NO in CCW_EVENT refuse unless STATUS is 'D' or 'P'. Set STATUS='C' and store CANCELLATION_REASON. If the event was Published, create an in-app notification and send an email with the reason to the same audience used by publish_event (owners from CCW_MEMBER_OWNER/CCW_MEMBER_PROFILE with LOGIN_ENABLED='Y' and active tenants with login unless AUDIENCE='O'; restricted by wing through CCW_UNIT_MASTER when AUDIENCE='W'). Return {"message":"Event cancelled"}.
# business_logic: Cancel the event and notify the audience


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
    reason = args.get('CANCELLATION_REASON')
    if is_empty(reason) or not str(reason).strip():
        return 'Cancellation reason is required'
    reason = str(reason).strip()
    event_no = args.get('EVENT_NO')
    if is_empty(event_no):
        return 'Event number is required'
    ev = db.query_one('SELECT * FROM ' + db.t('CCW_EVENT') + ' WHERE EVENT_NO = :n', {'n': event_no})
    if not ev:
        return 'Event not found'
    if ev['STATUS'] not in ('D', 'P'):
        return 'Only a Draft or Published event can be cancelled'
    was_published = ev['STATUS'] == 'P'

    db.update('CCW_EVENT', {'STATUS': 'C', 'CANCELLATION_REASON': reason}, {'EVENT_NO': event_no})

    if not was_published:
        return {'message': 'Event cancelled'}

    audience = ev['AUDIENCE']
    wing = ev['WING_CODE']
    if audience == 'W' and is_empty(wing):
        return {'message': 'Event cancelled',
                'warnings': [{'code': 'EVNOWING', 'type': 'W', 'message': 'No wing set for a wing-specific event; no one was notified'}]}
    emails = _audience_emails(audience, wing)
    start_s = str(ev['START_DATE_TIME'])[:19].replace('T', ' ')
    end_s = str(ev['END_DATE_TIME'])[:19].replace('T', ' ')
    subject = 'Event cancelled: ' + str(ev['TITLE'])
    body = ('Event cancelled: ' + str(ev['TITLE']) + '\nVenue: ' + str(ev['VENUE'])
            + '\nStart: ' + start_s + '\nEnd: ' + end_s + '\nReason: ' + reason)
    if emails:
        try:
            api.emit_event('event_cancelled', {
                'event_no': event_no, 'title': ev['TITLE'], 'venue': ev['VENUE'],
                'start_date_time': start_s, 'end_date_time': end_s,
                'cancellation_reason': reason,
                'subject': subject, 'message': body, 'recipients': emails})
        except Exception as e:
            return {'message': 'Event cancelled',
                    'warnings': [{'code': 'EVNOTIFY', 'type': 'W', 'message': 'Event cancelled but notification failed: ' + str(e)}]}
    return {'message': 'Event cancelled'}
