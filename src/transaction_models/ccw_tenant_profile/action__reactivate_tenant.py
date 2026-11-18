# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_tenant_profile
# event_type: action
# function_name: reactivate_tenant
# action_name: Re-activate
# language: python
# description: Re-activate a removed tenant profile
# functional_specification: Payload: the row (UNIT_NO). Require the stored TENANT_STATUS = 'R' and that TENANT_COMPANY_NAME, CONTACT_PERSON, CONTACT_NO_1 and TENANT_EMAIL are non-blank (the new tenant's details must have been entered by editing the Removed record first); otherwise return {"error": ...} naming the missing field. Also require the unit's CCW_MEMBER_PROFILE.OCCUPANCY_TYPE = 'R'. UPDATE CCW_TENANT_PROFILE SET TENANT_STATUS = 'A', REMOVED_ON = NULL, REMOVAL_REASON = NULL, LOGIN_ENABLED = 'N' unless the owner's TENANT_LOGIN_ALLOWED = 'Y' and the stored LOGIN_ENABLED = 'Y', SHOW_IN_DIRECTORY = 'N' unless the owner's SHOW_TENANT_IN_DIRECTORY = 'Y' and the stored value = 'Y', CHG_DATE = current timestamp WHERE UNIT_NO = the unit. Return {"message": "Tenant profile re-activated."}.
# business_logic: Re-activate a removed tenant profile


def run(args):
    unit = (args.get('UNIT_NO') or '').strip()
    if not unit:
        return {'error': 'Unit number is required.'}

    t = db.query_one(
        'SELECT TENANT_STATUS, TENANT_COMPANY_NAME, CONTACT_PERSON, CONTACT_NO_1, '
        'TENANT_EMAIL, LOGIN_ENABLED, SHOW_IN_DIRECTORY FROM ' + db.t('CCW_TENANT_PROFILE') +
        ' WHERE UNIT_NO = :u', {'u': unit})
    if not t:
        return {'error': 'Tenant profile not found for unit ' + unit + '.'}
    if (t['TENANT_STATUS'] or '').strip() != 'R':
        return {'error': 'Only a Removed tenant can be re-activated.'}

    for col, label in (('TENANT_COMPANY_NAME', 'Tenant company name'),
                       ('CONTACT_PERSON', 'Contact person'),
                       ('CONTACT_NO_1', 'Contact no 1'),
                       ('TENANT_EMAIL', 'Tenant email')):
        if is_empty((t[col] or '').strip()):
            return {'error': label + ' is required. Edit the Removed record to enter the new tenant details first.'}

    m = db.query_one(
        'SELECT OCCUPANCY_TYPE, TENANT_LOGIN_ALLOWED, SHOW_TENANT_IN_DIRECTORY FROM ' +
        db.t('CCW_MEMBER_PROFILE') + ' WHERE UNIT_NO = :u', {'u': unit})
    if not m or (m['OCCUPANCY_TYPE'] or '').strip() != 'R':
        return {'error': 'The unit is not marked Given on Rent in its Member Profile.'}

    login = 'Y' if ((m['TENANT_LOGIN_ALLOWED'] or '').strip() == 'Y'
                    and (t['LOGIN_ENABLED'] or '').strip() == 'Y') else 'N'
    show = 'Y' if ((m['SHOW_TENANT_IN_DIRECTORY'] or '').strip() == 'Y'
                   and (t['SHOW_IN_DIRECTORY'] or '').strip() == 'Y') else 'N'

    db.update('CCW_TENANT_PROFILE',
              {'TENANT_STATUS': 'A', 'REMOVED_ON': None, 'REMOVAL_REASON': None,
               'LOGIN_ENABLED': login, 'SHOW_IN_DIRECTORY': show,
               'CHG_DATE': now()},
              {'UNIT_NO': unit})
    return {'message': 'Tenant profile re-activated.'}
