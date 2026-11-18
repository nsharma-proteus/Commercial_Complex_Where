# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_business_category_master
# event_type: action_validation
# function_name: check_category_delete
# action_name: Delete
# language: python
# description: Block delete of a category used by profiles or queries
# functional_specification: Payload carries CATEGORY_CODE. If any row exists with BUSINESS_CATEGORY equal to this code in the Member Profile table (ccw_member_profile), the Tenant Profile table (ccw_tenant_profile), or with TARGET_BUSINESS_CATEGORY equal to it in the Business Query table (ccw_business_query), return {"error": "A category in use by a profile or query cannot be deleted. Make it Inactive instead."}; otherwise return None. Skip any of those tables that do not exist yet.
# business_logic: Block delete of a category used by profiles or queries

USAGE_CHECKS = [
    ('ccw_member_profile', 'BUSINESS_CATEGORY'),
    ('ccw_tenant_profile', 'BUSINESS_CATEGORY'),
    ('ccw_business_query', 'TARGET_BUSINESS_CATEGORY'),
]


def _in_use(table, column, code):
    try:
        row = db.query_one(
            'SELECT 1 AS x FROM ' + db.t(table) + ' WHERE ' + column + ' = :c',
            {'c': code})
    except Exception:
        # Table (or column) not deployed yet - nothing can reference the category.
        return False
    return row is not None


def run(args):
    code = args.get('CATEGORY_CODE')
    if is_empty(code):
        return None
    code = str(code).strip()

    for table, column in USAGE_CHECKS:
        if _in_use(table, column, code):
            return {"error": "A category in use by a profile or query cannot be deleted. Make it Inactive instead."}
    return None
