# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_business_query
# event_type: pre_commit
# function_name: generate_query_recipients
# language: python
# description: Generate recipients on first save
# functional_specification: Run only when action = 'add' (first save). From CCW_MEMBER_PROFILE where PROFILE_STATUS='A', SHOW_IN_DIRECTORY='Y' and BUSINESS_CATEGORY equals header TARGET_BUSINESS_CATEGORY, excluding UNIT_NO = header RAISED_BY_UNIT_NO, choose one recipient per unit: if OCCUPANCY_TYPE='O' (Owner Used) use the profile itself (BUSINESS_NAME, EMAIL as RECIPIENT_EMAIL); if OCCUPANCY_TYPE='R' (Given on Rent) use the tenant from CCW_TENANT_PROFILE for that UNIT_NO only when TENANT_STATUS='A', LOGIN_ENABLED='Y', SHOW_IN_DIRECTORY='Y' and the profile's SHOW_TENANT_IN_DIRECTORY='Y' and TENANT_LOGIN_ALLOWED='Y' (TENANT_COMPANY_NAME as BUSINESS_NAME, TENANT_EMAIL as RECIPIENT_EMAIL); otherwise skip the unit (a rented unit whose tenant is not shown falls back to the owner profile per the directory rule: use the owner profile). Insert rows into CCW_BQ_RECIPIENT (QUERY_NO = header QUERY_NO, LINE_NO numbered from 1, UNIT_NO, BUSINESS_NAME, RECIPIENT_EMAIL, FORWARDED_ON = now, VIEWED='N') inside the save transaction. If no recipient is found return {"warnings":[{"message":"No businesses found in this category; the query is saved without recipients."}]} and still save.
# business_logic: Generate recipients on first save


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
    category = _h(header, 'TARGET_BUSINESS_CATEGORY')
    raiser_unit = _h(header, 'RAISED_BY_UNIT_NO')
    if is_empty(query_no) or is_empty(category):
        return None

    profiles = db.query(
        'SELECT UNIT_NO, BUSINESS_NAME, EMAIL, OCCUPANCY_TYPE, SHOW_TENANT_IN_DIRECTORY, TENANT_LOGIN_ALLOWED '
        'FROM ' + db.t('CCW_MEMBER_PROFILE')
        + " WHERE PROFILE_STATUS = 'A' AND SHOW_IN_DIRECTORY = 'Y' AND BUSINESS_CATEGORY = :c "
        'ORDER BY UNIT_NO', {'c': category})

    line_no = 0
    for p in profiles:
        unit = p['UNIT_NO']
        if not is_empty(raiser_unit) and unit == raiser_unit:
            continue
        name = p['BUSINESS_NAME']
        email = p['EMAIL']
        if p['OCCUPANCY_TYPE'] == 'R' and p['SHOW_TENANT_IN_DIRECTORY'] == 'Y' and p['TENANT_LOGIN_ALLOWED'] == 'Y':
            t = db.query_one(
                'SELECT TENANT_COMPANY_NAME, TENANT_EMAIL FROM ' + db.t('CCW_TENANT_PROFILE')
                + " WHERE UNIT_NO = :u AND TENANT_STATUS = 'A' AND LOGIN_ENABLED = 'Y' AND SHOW_IN_DIRECTORY = 'Y'",
                {'u': unit})
            if t:
                name = t['TENANT_COMPANY_NAME']
                email = t['TENANT_EMAIL']
        # Owner Used units, and rented units whose tenant is not shown, use the owner profile.
        if is_empty(email):
            continue
        line_no += 1
        db.insert('CCW_BQ_RECIPIENT', {
            'QUERY_NO': query_no,
            'LINE_NO': line_no,
            'UNIT_NO': unit,
            'BUSINESS_NAME': name,
            'RECIPIENT_EMAIL': email,
            'FORWARDED_ON': now(),
            'VIEWED': 'N',
        })

    if line_no == 0:
        ignored = set(args.get('_ignore_warnings') or [])
        if 'BQ_NO_RECIPIENTS' not in ignored:
            # Informational prompt: never blocks, the query is still saved.
            return {'warnings': [{
                'code': 'BQ_NO_RECIPIENTS', 'type': 'P',
                'message': 'No businesses found in this category; the query is saved without recipients.'}]}
    return None
