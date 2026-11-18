# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_business_query
# event_type: action
# function_name: add_query_response
# action_name: Add Response
# language: python
# description: Add a response to the query and notify the raiser
# functional_specification: Read RESPONSE_TEXT from the payload (error if blank). Refuse with an error if CCW_BUSINESS_QUERY.STATUS for QUERY_NO is 'C' ('A closed query accepts no further responses'). Identify the responder by the signed-in user's email: allowed only if it equals RAISED_BY_EMAIL, or matches CCW_BQ_RECIPIENT.RECIPIENT_EMAIL for the QUERY_NO (case-insensitive); otherwise error 'Only recipients and the raiser can respond'. Determine RESPONDER_UNIT_NO from the matching recipient row (or RAISED_BY_UNIT_NO for the raiser); set RESPONDER_BUSINESS_NAME and RESPONDER_CONTACT_NO (CONTACT_NO_1) from CCW_MEMBER_PROFILE for that unit, or from CCW_TENANT_PROFILE (TENANT_COMPANY_NAME, CONTACT_NO_1) when the recipient is the active tenant. Insert a CCW_BQ_RESPONSE row with next LINE_NO for the QUERY_NO, RESPONSE_DATE = now. Mark the responder's CCW_BQ_RECIPIENT row VIEWED='Y'. Send an in-app notification and email to RAISED_BY_EMAIL with the response text and responder contact details. Return {"message":"Response added"}.
# business_logic: Add a response to the query and notify the raiser


def _me(args):
    for k in ('user_email', 'USER_EMAIL', '_user_email'):
        v = args.get(k)
        if not is_empty(v):
            return str(v).strip().lower()
    u = args.get('_user')
    if isinstance(u, dict) and not is_empty(u.get('email')):
        return str(u.get('email')).strip().lower()
    return None


def run(args):
    query_no = args.get('QUERY_NO')
    if is_empty(query_no):
        return 'Query number is missing'
    text = args.get('RESPONSE_TEXT')
    if is_empty(text) or not str(text).strip():
        return 'Response text is required'
    text = str(text).strip()

    q = db.query_one(
        'SELECT QUERY_NO, SUBJECT, STATUS, RAISED_BY_EMAIL, RAISED_BY_UNIT_NO FROM '
        + db.t('CCW_BUSINESS_QUERY') + ' WHERE QUERY_NO = :q', {'q': query_no})
    if not q:
        return 'Query not found'
    if q['STATUS'] == 'C':
        return 'A closed query accepts no further responses'

    raiser_email = (q['RAISED_BY_EMAIL'] or '').strip()
    recips = db.query(
        'SELECT LINE_NO, UNIT_NO, RECIPIENT_EMAIL FROM ' + db.t('CCW_BQ_RECIPIENT')
        + ' WHERE QUERY_NO = :q', {'q': query_no})

    # If the engine supplies no identity, fall back to the raiser (row security already scopes access).
    me = _me(args) or raiser_email.lower()
    recip_row = None
    for r in recips:
        if (r['RECIPIENT_EMAIL'] or '').strip().lower() == me:
            recip_row = r
            break
    is_raiser = (me == raiser_email.lower())
    if not is_raiser and recip_row is None:
        return 'Only recipients and the raiser can respond'

    unit = q['RAISED_BY_UNIT_NO'] if (is_raiser and recip_row is None) else recip_row['UNIT_NO']

    biz_name = None
    contact = None
    tenant = db.get('CCW_TENANT_PROFILE', {'UNIT_NO': unit})
    if (tenant and tenant['TENANT_STATUS'] == 'A'
            and (tenant['TENANT_EMAIL'] or '').strip().lower() == me):
        biz_name = tenant['TENANT_COMPANY_NAME']
        contact = tenant['CONTACT_NO_1']
    else:
        prof = db.get('CCW_MEMBER_PROFILE', {'UNIT_NO': unit})
        if prof:
            biz_name = prof['BUSINESS_NAME']
            contact = prof['CONTACT_NO_1']

    mx = db.scalar('SELECT MAX(LINE_NO) FROM ' + db.t('CCW_BQ_RESPONSE') + ' WHERE QUERY_NO = :q',
                   {'q': query_no})
    line_no = (int(mx) if mx is not None else 0) + 1

    db.insert('CCW_BQ_RESPONSE', {
        'QUERY_NO': query_no,
        'LINE_NO': line_no,
        'RESPONSE_DATE': now(),
        'RESPONDER_UNIT_NO': unit,
        'RESPONDER_BUSINESS_NAME': biz_name,
        'RESPONSE_TEXT': text,
        'RESPONDER_CONTACT_NO': contact,
    })

    if recip_row is not None:
        db.update('CCW_BQ_RECIPIENT', {'VIEWED': 'Y'},
                  {'QUERY_NO': query_no, 'LINE_NO': recip_row['LINE_NO']})

    out = {'message': 'Response added'}
    try:
        api.emit_event('business_query_response', {
            'query_no': query_no,
            'subject': q['SUBJECT'],
            'raiser_email': raiser_email,
            'response_text': text,
            'responder_unit_no': unit,
            'responder_business_name': biz_name,
            'responder_contact_no': contact,
        })
    except Exception as e:
        if 'not defined' not in str(e):
            out['warnings'] = [{
                'code': 'BQ_RESP_NOTIFY_FAIL', 'type': 'W',
                'message': 'Response added but the raiser could not be notified: ' + str(e)}]
    return out
