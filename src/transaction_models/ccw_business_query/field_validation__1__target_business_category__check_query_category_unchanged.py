# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_business_query
# event_type: field_validation
# function_name: check_query_category_unchanged
# form_no: 1
# field_name: target_business_category
# language: python
# description: Category cannot change after first save
# functional_specification: If _action = 'edit', read the stored TARGET_BUSINESS_CATEGORY of CCW_BUSINESS_QUERY for the payload QUERY_NO and return {"error":"Business category cannot be changed after the first save."} when the payload value differs. On 'add' return None.
# business_logic: Category cannot change after first save


def run(args):
    if args.get('_action') != 'edit':
        return None
    query_no = args.get('QUERY_NO')
    if is_empty(query_no):
        return None
    row = db.query_one(
        'SELECT TARGET_BUSINESS_CATEGORY FROM ' + db.t('CCW_BUSINESS_QUERY') + ' WHERE QUERY_NO = :q',
        {'q': query_no})
    if not row:
        return None
    stored = (row['TARGET_BUSINESS_CATEGORY'] or '').strip()
    new = (args.get('TARGET_BUSINESS_CATEGORY') or '').strip()
    if stored != new:
        return {'error': 'Business category cannot be changed after the first save.'}
    return None
