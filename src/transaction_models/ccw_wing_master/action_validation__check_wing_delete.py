# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_wing_master
# event_type: action_validation
# function_name: check_wing_delete
# action_name: Delete
# language: python
# description: Block delete of a wing that has units
# functional_specification: Payload carries WING_CODE. If any row exists in the unit master table (ccw_unit_master, column WING_CODE) with WING_CODE equal to this wing's code, return {"error": "A wing that has Units cannot be deleted. Make it Inactive instead."}; otherwise return None. If the unit master table does not exist yet, return None.
# business_logic: Block delete of a wing that has units


def run(args):
    code = args.get('WING_CODE')
    if is_empty(code):
        return None
    code = str(code).strip()
    try:
        row = db.query_one(
            'SELECT 1 AS x FROM ' + db.t('ccw_unit_master') + ' WHERE wing_code = :c',
            {'c': code})
    except Exception as e:
        msg = str(e).lower()
        # Unit master table not deployed yet -> nothing can reference the wing.
        if 'does not exist' in msg or 'no such table' in msg or 'ora-00942' in msg or 'undefined table' in msg or 'not found' in msg:
            return None
        raise
    if row:
        return {'error': 'A wing that has Units cannot be deleted. Make it Inactive instead.'}
    return None
