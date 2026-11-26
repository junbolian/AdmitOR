# IR: {
#   "sets": {"staff_types": ["fulltime", "parttime"]},
#   "params": ["profit_per_pair", "fulltime_sales_rate", "parttime_sales_rate", "fulltime_salary", "parttime_salary", "fulltime_overtime_pay", "parttime_overtime_pay", "fulltime_hours", "parttime_hours", "sales_target", "fulltime_overtime_limit"],
#   "structural_constants": {"fulltime_count": 5, "parttime_count": 4, "fulltime_idle_weight": 2},
#   "variables": {"regular_hours[staff_types]": "continuous_nonnegative_aggregate_hours", "overtime_hours[staff_types]": "continuous_nonnegative_aggregate_hours", "idle_hours[staff_types]": "continuous_nonnegative_aggregate_hours", "sales_shortfall": "continuous_nonnegative_pairs", "sales_surplus": "continuous_nonnegative_pairs", "overtime_slack": "continuous_nonnegative_hours", "overtime_excess": "continuous_nonnegative_hours"},
#   "expressions": {"sales": "sum(sales_rate[t]*(regular_hours[t]+overtime_hours[t]))", "payroll": "sum(salary[t]*regular_hours[t]+overtime_pay[t]*overtime_hours[t])", "net_profit": "profit_per_pair*sales-payroll"},
#   "constraints": ["regular_hours[t]+idle_hours[t]=staff_count[t]*standard_hours[t] for each t", "sales+sales_shortfall-sales_surplus=sales_target", "overtime_hours[fulltime]+overtime_slack-overtime_excess=fulltime_overtime_limit", "after each nonfinal priority solve, fix that priority expression at its attained optimum"],
#   "objective": {"sense": "lexicographic_minimize", "priorities": ["sales_shortfall", "overtime_excess", "2*idle_hours[fulltime]+idle_hours[parttime]", "sum(overtime_hours[t])"], "returned_objective": "final_priority_total_overtime_hours"}
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the four goals in strict priority order p1, p2, p3, p4.

    Hours and the full-time overtime limit are aggregated across employees
    of each type. Sales above the target are permitted. Economic quantities
    are reported as model expressions; the stated goals do not prioritize
    maximizing profit or minimizing payroll.
    """
    model = pyo.ConcreteModel()

    model.staff_types = pyo.Set(
        initialize=["fulltime", "parttime"], ordered=True
    )
    model.staff_count = pyo.Param(
        model.staff_types,
        initialize={"fulltime": 5, "parttime": 4},
        within=pyo.PositiveIntegers,
    )

    model.profit_per_pair = pyo.Param(
        initialize=params["profit_per_pair"], within=pyo.NonNegativeReals
    )
    model.sales_rate = pyo.Param(
        model.staff_types,
        initialize={
            "fulltime": params["fulltime_sales_rate"],
            "parttime": params["parttime_sales_rate"],
        },
        within=pyo.NonNegativeReals,
    )
    model.salary = pyo.Param(
        model.staff_types,
        initialize={
            "fulltime": params["fulltime_salary"],
            "parttime": params["parttime_salary"],
        },
        within=pyo.NonNegativeReals,
    )
    model.overtime_pay = pyo.Param(
        model.staff_types,
        initialize={
            "fulltime": params["fulltime_overtime_pay"],
            "parttime": params["parttime_overtime_pay"],
        },
        within=pyo.NonNegativeReals,
    )
    model.standard_hours = pyo.Param(
        model.staff_types,
        initialize={
            "fulltime": params["fulltime_hours"],
            "parttime": params["parttime_hours"],
        },
        within=pyo.NonNegativeReals,
    )
    model.sales_target = pyo.Param(
        initialize=params["sales_target"], within=pyo.NonNegativeReals
    )
    model.fulltime_overtime_limit = pyo.Param(
        initialize=params["fulltime_overtime_limit"],
        within=pyo.NonNegativeReals,
    )

    model.regular_hours = pyo.Var(
        model.staff_types, domain=pyo.NonNegativeReals
    )
    model.overtime_hours = pyo.Var(
        model.staff_types, domain=pyo.NonNegativeReals
    )
    model.idle_hours = pyo.Var(
        model.staff_types, domain=pyo.NonNegativeReals
    )
    model.sales_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.sales_surplus = pyo.Var(domain=pyo.NonNegativeReals)
    model.overtime_slack = pyo.Var(domain=pyo.NonNegativeReals)
    model.overtime_excess = pyo.Var(domain=pyo.NonNegativeReals)

    model.sales = pyo.Expression(
        expr=sum(
            model.sales_rate[staff_type]
            * (
                model.regular_hours[staff_type]
                + model.overtime_hours[staff_type]
            )
            for staff_type in model.staff_types
        )
    )
    model.payroll = pyo.Expression(
        expr=sum(
            model.salary[staff_type] * model.regular_hours[staff_type]
            + model.overtime_pay[staff_type]
            * model.overtime_hours[staff_type]
            for staff_type in model.staff_types
        )
    )
    model.net_profit = pyo.Expression(
        expr=model.profit_per_pair * model.sales - model.payroll
    )

    def employment_balance_rule(instance, staff_type):
        return (
            instance.regular_hours[staff_type]
            + instance.idle_hours[staff_type]
            == instance.staff_count[staff_type]
            * instance.standard_hours[staff_type]
        )

    model.employment_balance = pyo.Constraint(
        model.staff_types, rule=employment_balance_rule
    )
    model.sales_goal = pyo.Constraint(
        expr=model.sales + model.sales_shortfall - model.sales_surplus
        == model.sales_target
    )
    model.fulltime_overtime_goal = pyo.Constraint(
        expr=model.overtime_hours["fulltime"]
        + model.overtime_slack
        - model.overtime_excess
        == model.fulltime_overtime_limit
    )

    priority_expressions = (
        model.sales_shortfall,
        model.overtime_excess,
        2 * model.idle_hours["fulltime"] + model.idle_hours["parttime"],
        sum(
            model.overtime_hours[staff_type]
            for staff_type in model.staff_types
        ),
    )

    model.priority_fixes = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=priority_expressions[0], sense=pyo.minimize
    )

    for priority_index, priority_expression in enumerate(priority_expressions):
        model.goal_objective.set_value(priority_expression)

        # Clear prior solutions so a failed solve cannot expose stale values.
        for variable in model.component_data_objects(pyo.Var):
            variable.set_value(None)

        try:
            Highs().solve(model)
        except RuntimeError:
            return {"objective": None, "status": "solver_failed"}

        # Success is determined only by retrieving the objective value.
        try:
            obj_val = float(pyo.value(model.goal_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if priority_index < len(priority_expressions) - 1:
            model.priority_fixes.add(priority_expression == obj_val)

    return {"objective": obj_val, "status": "optimal"}