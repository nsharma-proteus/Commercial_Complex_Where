# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_member_profile
# event_type: form_validation
# function_name: check_occupancy_change
# form_no: 1
# language: python
# description: Block Given on Rent to Owner Used while tenant is Active
# functional_specification: Runs on form save. Only when _action = 'edit'. Read the stored CCW_MEMBER_PROFILE row for UNIT_NO. If the stored OCCUPANCY_TYPE = 'R' and the incoming OCCUPANCY_TYPE = 'O', check CCW_TENANT_PROFILE for a row with UNIT_NO = this unit and TENANT_STATUS = 'A' (Active). If the table CCW_TENANT_PROFILE does not exist yet, pass. If an active tenant exists return {"error": "Occupancy cannot be changed to Owner Used while the Tenant Profile is Active. Use Remove Tenant first."}; otherwise return nothing.
# business_logic: Block Given on Rent to Owner Used while tenant is Active


def run(args):
    if args.get('_action') != 'edit':
        return None
    unit = args.get('UNIT_NO')
    if is_empty(unit) or args.get('OCCUPANCY_TYPE') != 'O':
        return None
    stored = db.query_one(
        'SELECT OCCUPANCY_TYPE FROM ' + db.t('CCW_MEMBER_PROFILE') + ' WHERE UNIT_NO = :u',
        {'u': unit})
    if not stored or stored['OCCUPANCY_TYPE'] != 'R':
        return None
    if db.scalar('SELECT to_regclass(:n)', {'n': db.t('CCW_TENANT_PROFILE')}) is None:
        return None
    cnt = db.scalar(
        'SELECT COUNT(*) FROM ' + db.t('CCW_TENANT_PROFILE') +
        ' WHERE UNIT_NO = :u AND TENANT_STATUS = :s',
        {'u': unit, 's': 'A'})
    if to_number(cnt) > 0:
        return {'error': 'Occupancy cannot be changed to Owner Used while the Tenant Profile is Active. Use Remove Tenant first.'}
    return None
