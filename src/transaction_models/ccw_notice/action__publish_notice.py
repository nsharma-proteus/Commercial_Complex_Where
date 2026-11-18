# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_notice
# event_type: action
# function_name: publish_notice
# action_name: Publish
# language: python
# description: Publish the notice and notify the audience
# functional_specification: Set STATUS='P' on CCW_NOTICE for the given NOTICE_NO and stamp PUBLISHED_BY with the signed-in user's email. Create an in-app notification and send an email to the intended audience: owners (CCW_MEMBER_OWNER.OWNER_EMAIL joined to CCW_MEMBER_PROFILE on UNIT_NO where PROFILE_STATUS='A' and LOGIN_ENABLED='Y') plus, unless AUDIENCE='O', active tenants with login (CCW_TENANT_PROFILE.TENANT_EMAIL where TENANT_STATUS='A' and LOGIN_ENABLED='Y'). When AUDIENCE='W' restrict to units (CCW_UNIT_MASTER) whose WING_CODE equals the notice WING_CODE. Return {"message":"Notice published"}.
# business_logic: Publish the notice and notify the audience


def run(args):
    notice_no = args.get('NOTICE_NO')
    if is_empty(notice_no):
        return 'Notice number is missing'

    notice = db.query_one(
        'SELECT NOTICE_NO, TITLE, STATUS, AUDIENCE, WING_CODE, PUBLISH_DATE, EXPIRY_DATE, IS_IMPORTANT, PUBLISHED_BY '
        'FROM ' + db.t('CCW_NOTICE') + ' WHERE NOTICE_NO = :n',
        {'n': notice_no})
    if not notice:
        return 'Notice not found'
    if notice['STATUS'] == 'P':
        return 'Notice is already published'
    if notice['STATUS'] == 'W':
        return 'A withdrawn notice cannot be published again'

    audience = notice['AUDIENCE']
    wing = notice['WING_CODE']
    if audience == 'W' and is_empty(wing):
        return 'Wing is required for a Specific Wing notice'

    publisher = coalesce(args.get('PUBLISHED_BY'), notice['PUBLISHED_BY'])
    if is_empty(publisher):
        publisher = None

    # Audience: owners
    params = {}
    sql = ('SELECT DISTINCT mo.OWNER_EMAIL AS EMAIL FROM ' + db.t('CCW_MEMBER_OWNER') + ' mo '
           'JOIN ' + db.t('CCW_MEMBER_PROFILE') + ' mp ON mp.UNIT_NO = mo.UNIT_NO ')
    if audience == 'W':
        sql += 'JOIN ' + db.t('CCW_UNIT_MASTER') + ' um ON um.UNIT_NO = mo.UNIT_NO '
    sql += "WHERE mp.PROFILE_STATUS = 'A' AND mo.LOGIN_ENABLED = 'Y'"
    if audience == 'W':
        sql += ' AND um.WING_CODE = :w'
        params['w'] = wing
    emails = [r['EMAIL'] for r in db.query(sql, params) if not is_empty(r['EMAIL'])]

    # Audience: active tenants with login (not for Owners Only)
    if audience != 'O':
        tparams = {}
        tsql = 'SELECT DISTINCT tp.TENANT_EMAIL AS EMAIL FROM ' + db.t('CCW_TENANT_PROFILE') + ' tp '
        if audience == 'W':
            tsql += 'JOIN ' + db.t('CCW_UNIT_MASTER') + ' um ON um.UNIT_NO = tp.UNIT_NO '
        tsql += "WHERE tp.TENANT_STATUS = 'A' AND tp.LOGIN_ENABLED = 'Y'"
        if audience == 'W':
            tsql += ' AND um.WING_CODE = :w'
            tparams['w'] = wing
        emails += [r['EMAIL'] for r in db.query(tsql, tparams) if not is_empty(r['EMAIL'])]

    recipients = sorted(set(emails))

    upd = {'STATUS': 'P'}
    if publisher is not None:
        upd['PUBLISHED_BY'] = publisher
    db.update('CCW_NOTICE', upd, {'NOTICE_NO': notice_no})

    out = {'message': 'Notice published'}
    if not recipients:
        return out
    try:
        api.emit_event('notice_published', {
            'notice_no': notice_no,
            'title': notice['TITLE'],
            'audience': audience,
            'wing_code': wing,
            'is_important': notice['IS_IMPORTANT'],
            'publish_date': str(notice['PUBLISH_DATE']) if notice['PUBLISH_DATE'] else None,
            'expiry_date': str(notice['EXPIRY_DATE']) if notice['EXPIRY_DATE'] else None,
            'recipients': recipients,
        })
    except Exception as e:
        if 'not defined' in str(e):
            # No Integration Design event wired yet: the notice is published; delivery is skipped.
            return out
        out['warnings'] = [{
            'code': 'NTPUB_NOTIFY_FAIL', 'type': 'W',
            'message': 'Notice published but notifications could not be sent: ' + str(e)}]
    return out
