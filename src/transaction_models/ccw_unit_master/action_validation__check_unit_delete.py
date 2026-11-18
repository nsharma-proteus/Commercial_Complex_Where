# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_unit_master
# event_type: action_validation
# function_name: check_unit_delete
# action_name: Delete
# language: python
# description: Block delete of a unit that has a Member Profile
# functional_specification: Payload carries UNIT_NO. If any row exists in the Member Profile table (ccw_member_profile, column UNIT_NO) with UNIT_NO equal to this unit, return {"error": "A unit with a Member Profile cannot be deleted."}; otherwise return None. If the member profile table does not exist yet, return None.
# business_logic: Block delete of a unit that has a Member Profile


def run(args):
    unit_no = args.get('UNIT_NO')
    if is_empty(unit_no):
        return None
    unit_no = str(unit_no).strip()

    try:
        row = db.query_one(
            'SELECT 1 AS x FROM ' + db.t('ccw_member_profile') + ' WHERE unit_no = :u',
            {'u': unit_no})
    except Exception as e:
        msg = str(e).lower()
        # Member Profile table not deployed yet -> nothing can reference the unit.
        if 'does not exist' in msg or 'no such table' in msg or 'ora-00942' in msg or 'undefined table' in msg:
            return None
        raise

    if row:
        return {'error': 'A unit with a Member Profile cannot be deleted.'}
    return None
