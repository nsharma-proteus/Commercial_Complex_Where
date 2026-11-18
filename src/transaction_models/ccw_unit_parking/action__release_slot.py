# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_unit_parking
# event_type: action
# function_name: release_slot
# action_name: Release Slot
# language: python
# description: Release the parking slot
# functional_specification: Given the slot (PARKING_SLOT_NO), set CCW_UNIT_PARKING.STATUS='R' and stamp chg columns. Return {error} if status is already 'R' or if any row exists in CCW_UNIT_PARKING_VEHICLE for the slot (vehicles must be removed first). Return {message} confirming release.
# business_logic: Release the parking slot

def run(args):
    slot = args.get('PARKING_SLOT_NO')
    slot = str(slot).strip() if slot is not None else ''
    if not slot:
        return {'error': 'Parking slot number is required.'}

    row = db.query_one(
        'SELECT status FROM ' + db.t('CCW_UNIT_PARKING') + ' WHERE parking_slot_no = :s',
        {'s': slot})
    if not row:
        return {'error': 'Parking slot ' + slot + ' does not exist.'}
    if str(row['status']).strip() == 'R':
        return {'error': 'Parking slot ' + slot + ' is already released.'}

    cnt = db.scalar(
        'SELECT COUNT(*) FROM ' + db.t('CCW_UNIT_PARKING_VEHICLE') + ' WHERE parking_slot_no = :s',
        {'s': slot})
    if to_number(cnt) > 0:
        return {'error': 'Parking slot ' + slot + ' still has vehicles registered. Remove the vehicles before releasing the slot.'}

    upd = {'STATUS': 'R', 'CHG_DATE': now()}
    if not_empty(args.get('CHG_USER')):
        upd['CHG_USER'] = args.get('CHG_USER')
    if not_empty(args.get('CHG_TERM')):
        upd['CHG_TERM'] = args.get('CHG_TERM')
    db.update('CCW_UNIT_PARKING', upd, {'PARKING_SLOT_NO': slot})

    return {'message': 'Parking slot ' + slot + ' has been released.'}
