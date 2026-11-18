# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_tenant_profile
# event_type: action
# function_name: remove_tenant
# action_name: Remove Tenant
# language: python
# description: Remove the tenant from the unit
# functional_specification: Payload: the row (UNIT_NO ...) plus REMOVAL_REASON captured from the user. If REMOVAL_REASON is blank (after trimming) return {"error": "A removal reason is required."}. If the stored TENANT_STATUS is not 'A' return {"error": "Only an Active tenant can be removed."}. UPDATE CCW_TENANT_PROFILE SET TENANT_STATUS = 'R', LOGIN_ENABLED = 'N', SHOW_IN_DIRECTORY = 'N', REMOVED_ON = current timestamp, REMOVAL_REASON = the reason, CHG_DATE = current timestamp WHERE UNIT_NO = the unit. Do not touch CCW_UNIT_MASTER (occupancy stays Given on Rent) or any guest entries / facility requests. Return {"message": "Tenant removed from unit <UNIT_NO>."}. Access: the button is granted only to the unit's owners and management (never to tenants).
# business_logic: Remove the tenant from the unit


def run(args):
    unit = (args.get('UNIT_NO') or '').strip()
    reason = (args.get('REMOVAL_REASON') or '').strip()
    if not reason:
        return {'error': 'A removal reason is required.'}
    if not unit:
        return {'error': 'Unit number is required.'}

    t = db.query_one('SELECT TENANT_STATUS FROM ' + db.t('CCW_TENANT_PROFILE') +
                     ' WHERE UNIT_NO = :u', {'u': unit})
    if not t or (t['TENANT_STATUS'] or '').strip() != 'A':
        return {'error': 'Only an Active tenant can be removed.'}

    db.update('CCW_TENANT_PROFILE',
              {'TENANT_STATUS': 'R', 'LOGIN_ENABLED': 'N', 'SHOW_IN_DIRECTORY': 'N',
               'REMOVED_ON': now(), 'REMOVAL_REASON': reason, 'CHG_DATE': now()},
              {'UNIT_NO': unit})
    return {'message': 'Tenant removed from unit ' + unit + '.'}
