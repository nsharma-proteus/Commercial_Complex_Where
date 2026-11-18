# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_member_profile
# event_type: cross_update
# function_name: apply_tenant_flags
# form_no: 1
# language: python
# description: Apply tenant access flags to the Tenant Profile
# functional_specification: Fires on every save of the header row. If table CCW_TENANT_PROFILE does not exist or has no row for UNIT_NO, do nothing. Otherwise for that unit: if TENANT_LOGIN_ALLOWED = 'N' (or OCCUPANCY_TYPE <> 'R') set CCW_TENANT_PROFILE.LOGIN_ENABLED = 'N'; if SHOW_TENANT_IN_DIRECTORY = 'N' (or OCCUPANCY_TYPE <> 'R') set CCW_TENANT_PROFILE.SHOW_IN_DIRECTORY = 'N'. The tenant's edit right (ALLOW_TENANT_TO_UPDATE_PROFILE) is read live from this profile, so it needs no write. Never turn a flag to 'Y' automatically.
# business_logic: Apply tenant access flags to the Tenant Profile


def run(args):
    unit = args.get('UNIT_NO')
    if is_empty(unit):
        return None
    if db.scalar('SELECT to_regclass(:n)', {'n': db.t('CCW_TENANT_PROFILE')}) is None:
        return None
    cnt = db.scalar('SELECT COUNT(*) FROM ' + db.t('CCW_TENANT_PROFILE') + ' WHERE UNIT_NO = :u', {'u': unit})
    if to_number(cnt) == 0:
        return None

    occ = args.get('OCCUPANCY_TYPE')
    not_rented = occ != 'R'
    sets = {}
    if not_rented or args.get('TENANT_LOGIN_ALLOWED') == 'N':
        sets['LOGIN_ENABLED'] = 'N'
    if not_rented or args.get('SHOW_TENANT_IN_DIRECTORY') == 'N':
        sets['SHOW_IN_DIRECTORY'] = 'N'
    if sets:
        db.update('CCW_TENANT_PROFILE', sets, {'UNIT_NO': unit})
    return None
