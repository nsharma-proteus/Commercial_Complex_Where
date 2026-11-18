# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_member_profile
# event_type: action_validation
# function_name: check_profile_deletable
# action_name: Delete
# language: python
# description: Block delete with open requests or Active tenant
# functional_specification: Input: the profile row (UNIT_NO). If table CCW_TENANT_PROFILE exists and has a row for UNIT_NO with TENANT_STATUS = 'A', return {"error": "Unit <UNIT_NO> has an Active tenant. Remove the tenant first."}. If table CCW_FACILITY_REQUEST exists and has rows for UNIT_NO with STATUS NOT IN ('C','X') (not Closed/Cancelled; confirm the real status codes in that table), return {"error": "Unit <UNIT_NO> has open facility requests."}. A table that does not exist yet is skipped. Otherwise return nothing.
# business_logic: Block delete with open requests or Active tenant


def _table_exists(name):
    return db.scalar('SELECT to_regclass(:n)', {'n': db.t(name)}) is not None


def run(args):
    unit = args.get('UNIT_NO')
    if is_empty(unit):
        return None

    if _table_exists('CCW_TENANT_PROFILE'):
        cnt = db.scalar(
            'SELECT COUNT(*) FROM ' + db.t('CCW_TENANT_PROFILE') +
            ' WHERE UNIT_NO = :u AND TENANT_STATUS = :s',
            {'u': unit, 's': 'A'})
        if to_number(cnt) > 0:
            return {'error': 'Unit ' + str(unit) + ' has an Active tenant. Remove the tenant first.'}

    if _table_exists('CCW_FACILITY_REQUEST'):
        cnt = db.scalar(
            'SELECT COUNT(*) FROM ' + db.t('CCW_FACILITY_REQUEST') +
            ' WHERE UNIT_NO = :u AND STATUS NOT IN (:c, :x)',
            {'u': unit, 'c': 'C', 'x': 'X'})
        if to_number(cnt) > 0:
            return {'error': 'Unit ' + str(unit) + ' has open facility requests.'}

    return None
