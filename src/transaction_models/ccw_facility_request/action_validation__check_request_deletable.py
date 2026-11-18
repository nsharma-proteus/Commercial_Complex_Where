# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_facility_request
# event_type: action_validation
# function_name: check_request_deletable
# action_name: Delete
# language: python
# description: Delete guard
# functional_specification: Return {"error":"A request with updates cannot be deleted."} when any row exists in CCW_FR_UPDATE for the payload REQUEST_NO; otherwise None.
# business_logic: Delete guard


def run(args):
    no = args.get('REQUEST_NO')
    if is_empty(no):
        return None
    n = db.scalar('SELECT COUNT(*) FROM ' + db.t('CCW_FR_UPDATE') + ' WHERE REQUEST_NO = :n', {'n': no})
    if to_number(n) > 0:
        return {'error': 'A request with updates cannot be deleted.'}
    return None
