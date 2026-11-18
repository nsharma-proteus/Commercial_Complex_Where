# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_member_profile
# event_type: cross_update
# function_name: sync_unit_occupancy
# form_no: 1
# language: python
# description: Update Unit Master occupancy status on save
# functional_specification: Fires on every save (add/update) of the header row. UPDATE CCW_UNIT_MASTER SET OCCUPANCY_STATUS = 'O' WHERE UNIT_NO = <UNIT_NO> when OCCUPANCY_TYPE = 'O' (Owner Used), or 'R' when OCCUPANCY_TYPE = 'R' (Given on Rent). Return {"error": ...} if no unit row was updated (rowcount 0).
# business_logic: Update Unit Master occupancy status on save


def run(args):
    unit = args.get('UNIT_NO')
    occ = args.get('OCCUPANCY_TYPE')
    if is_empty(unit) or occ not in ('O', 'R'):
        return None
    cnt = db.scalar('SELECT COUNT(*) FROM ' + db.t('CCW_UNIT_MASTER') + ' WHERE UNIT_NO = :u', {'u': unit})
    if to_number(cnt) == 0:
        return {'error': 'Unit ' + str(unit) + ' not found in Unit Master; occupancy status not updated.'}
    db.update('CCW_UNIT_MASTER', {'OCCUPANCY_STATUS': occ}, {'UNIT_NO': unit})
    return None
