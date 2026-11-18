# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_notice
# event_type: action
# function_name: withdraw_notice
# action_name: Withdraw
# language: python
# description: Withdraw a published notice
# functional_specification: Set STATUS='W' on CCW_NOTICE for the given NOTICE_NO so it no longer shows on the Notice Board. Return {"message":"Notice withdrawn"}.
# business_logic: Withdraw a published notice


def run(args):
    notice_no = args.get('NOTICE_NO')
    if is_empty(notice_no):
        return 'Notice number is missing'
    status = db.scalar('SELECT STATUS FROM ' + db.t('CCW_NOTICE') + ' WHERE NOTICE_NO = :n',
                       {'n': notice_no})
    if status is None:
        return 'Notice not found'
    if status == 'W':
        return 'Notice is already withdrawn'
    if status != 'P':
        return 'Only a published notice can be withdrawn'
    db.update('CCW_NOTICE', {'STATUS': 'W'}, {'NOTICE_NO': notice_no})
    return {'message': 'Notice withdrawn'}
