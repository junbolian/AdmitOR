# IR: {"sets":{"staff_types":["full_time","part_time"],"priorities":[1,2,3]},"params":["profit_per_pair","full_time_count","part_time_count","full_time_monthly_hours","part_time_monthly_hours","full_time_sales_rate","part_time_sales_rate","full_time_wage","part_time_wage","full_time_overtime_pay","part_time_overtime_pay","sales_target"],"variables":{"regular_hours[t]":"nonnegative continuous","idle_hours[t]":"nonnegative continuous","overtime_hours[t]":"nonnegative continuous","sales_shortfall":"nonnegative continuous","sales_surplus":"nonnegative continuous"},"constraints":["regular_hours[t]+idle_hours[t]=count[t]*monthly_hours[t] for each staff type t","sum(sales_rate[t]*(regular_hours[t]+overtime_hours[t]))+sales_shortfall-sales_surplus=sales_target","after each of priorities 1 and 2, fix its objective expression to its attained optimum"],"objective":"lexicographically minimize (sales_shortfall, sum(idle_hours[t]), sum(overtime_hours[t])); return the final overtime objective"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.staff_types = pyo.Set(
        initialize=["full_time", "part_time"], ordered=True
    )

    model.profit_per_pair = pyo.Param(
        initialize=params["profit_per_pair"]
    )
    model.full_time_count = pyo.Param(
        initialize=params["full_time_count"]
    )
    model.part_time_count = pyo.Param(
        initialize=params["part_time_count"]
    )
    model.full_time_monthly_hours = pyo.Param(
        initialize=params["full_time_monthly_hours"]
    )
    model.part_time_monthly_hours = pyo.Param(
        initialize=params["part_time_monthly_hours"]
    )
    model.full_time_sales_rate = pyo.Param(
        initialize=params["full_time_sales_rate"]
    )
    model.part_time_sales_rate = pyo.Param(
        initialize=params["part_time_sales_rate"]
    )
    model.full_time_wage = pyo.Param(
        initialize=params["full_time_wage"]
    )
    model.part_time_wage = pyo.Param(
        initialize=params["part_time_wage"]
    )
    model.full_time_overtime_pay = pyo.Param(
        initialize=params["full_time_overtime_pay"]
    )
    model.part_time_overtime_pay = pyo.Param(
        initialize=params["part_time_overtime_pay"]
    )
    model.sales_target = pyo.Param(
        initialize=params["sales_target"]
    )

    # Hours are aggregated across the fixed employees of each staff type.
    capacity = {
        "full_time": (
            model.full_time_count * model.full_time_monthly_hours
        ),
        "part_time": (
            model.part_time_count * model.part_time_monthly_hours
        ),
    }
    sales_rate = {
        "full_time": model.full_time_sales_rate,
        "part_time": model.part_time_sales_rate,
    }

    model.regular_hours = pyo.Var(
        model.staff_types, domain=pyo.NonNegativeReals
    )
    model.idle_hours = pyo.Var(
        model.staff_types, domain=pyo.NonNegativeReals
    )
    model.overtime_hours = pyo.Var(
        model.staff_types, domain=pyo.NonNegativeReals
    )
    model.sales_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.sales_surplus = pyo.Var(domain=pyo.NonNegativeReals)

    def employment_balance_rule(instance, staff_type):
        return (
            instance.regular_hours[staff_type]
            + instance.idle_hours[staff_type]
            == capacity[staff_type]
        )

    model.employment_balance = pyo.Constraint(
        model.staff_types, rule=employment_balance_rule
    )

    model.sales_balance = pyo.Constraint(
        expr=(
            sum(
                sales_rate[staff_type]
                * (
                    model.regular_hours[staff_type]
                    + model.overtime_hours[staff_type]
                )
                for staff_type in model.staff_types
            )
            + model.sales_shortfall
            - model.sales_surplus
            == model.sales_target
        )
    )

    # Interpret p1, p2, p3 as strict, descending priorities.
    # Achieving the sales target means meeting or exceeding it.
    # Full employment means using all available regular working hours.
    # Monetary inputs are retained above but do not enter these stated goals.
    priority_expressions = (
        model.sales_shortfall,
        sum(
            model.idle_hours[staff_type]
            for staff_type in model.staff_types
        ),
        sum(
            model.overtime_hours[staff_type]
            for staff_type in model.staff_types
        ),
    )

    model.priority_locks = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=priority_expressions[0], sense=pyo.minimize
    )

    for priority_index, expression in enumerate(priority_expressions):
        model.goal_objective.set_value(expression)

        try:
            Highs().solve(model)
        except RuntimeError as exc:
            # Appsi raises this when automatic solution loading cannot find
            # a feasible solution. Unexpected runtime errors propagate.
            if "a feasible solution was not found" in str(exc).lower():
                return {
                    "objective": None,
                    "status": "no_feasible_solution",
                }
            raise

        # Objective retrieval is the sole success test.
        try:
            obj_val = float(pyo.value(model.goal_objective))
        except ValueError:
            return {
                "objective": None,
                "status": "objective_unavailable",
            }

        if priority_index < len(priority_expressions) - 1:
            model.priority_locks.add(expression == obj_val)

    # The returned objective is minimum overtime hours after satisfying
    # the two higher-priority goals as well as possible.
    return {"objective": obj_val, "status": "optimal"}