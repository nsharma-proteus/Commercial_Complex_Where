# project: Commercial_Complex_Where
# object_type: T
# object_name: ccw_banner_rate_plan_master
# event_type: action_validation
# function_name: check_plan_not_used
# action_name: Delete
# language: python
# description: Block delete when the plan is used in any booking
# functional_specification: Input: the plan row (PLAN_CODE). If table CCW_BANNER_BOOKING does not yet exist, return nothing (pass). Otherwise count rows in CCW_BANNER_BOOKING that reference this PLAN_CODE (the booking's rate-plan column, expected PLAN_CODE). If count > 0 return {"error": "Plan <PLAN_CODE> is used in <n> banner booking(s) and cannot be deleted. Make it Inactive instead."}; else return nothing.
# business_logic: Block delete when the plan is used in any booking


def run(args):
    plan = args.get('PLAN_CODE')
    if is_empty(plan):
        return None
    plan = str(plan).strip()

    try:
        n = db.scalar(
            'SELECT COUNT(*) FROM ' + db.t('CCW_BANNER_BOOKING') + ' WHERE PLAN_CODE = :p',
            {'p': plan})
    except Exception as e:
        msg = str(e).lower()
        # Booking table not deployed yet (or column not there yet): nothing can reference the plan.
        if ('does not exist' in msg or 'ora-00942' in msg or 'no such table' in msg
                or "doesn't exist" in msg or 'undefined table' in msg or 'not found' in msg):
            return None
        raise

    n = int(to_number(n) or 0)
    if n > 0:
        return {'error': 'Plan ' + plan + ' is used in ' + str(n) +
                ' banner booking(s) and cannot be deleted. Make it Inactive instead.'}
    return None
