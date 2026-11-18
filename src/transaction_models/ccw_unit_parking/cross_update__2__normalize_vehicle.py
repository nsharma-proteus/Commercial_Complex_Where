# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_unit_parking
# event_type: cross_update
# function_name: normalize_vehicle
# language: python
# description: Store vehicle number upper case without spaces; unique among vehicles

def run(args):
    raw = args.get('vehicle_no') or args.get('VEHICLE_NO') or ''
    vno = ''.join(str(raw).split()).upper()
    slot = args.get('parking_slot_no') or args.get('PARKING_SLOT_NO')
    line = args.get('line_no') or args.get('LINE_NO')
    if not vno:
        return {'error': 'Vehicle No is required.'}
    t = db.t('CCW_UNIT_PARKING_VEHICLE')
    dup = db.scalar(
        'SELECT COUNT(*) FROM ' + t + " WHERE UPPER(REPLACE(vehicle_no, ' ', '')) = :v "
        'AND NOT (parking_slot_no = :s AND line_no = :l)',
        {'v': vno, 's': slot, 'l': line})
    if to_number(dup) > 0:
        return {'error': 'Vehicle ' + vno + ' is already registered.'}
    db.update('CCW_UNIT_PARKING_VEHICLE', {'VEHICLE_NO': vno},
              {'PARKING_SLOT_NO': slot, 'LINE_NO': line})
    return None
