import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_pair = params["profit_per_pair"]
    full_time_count = params["full_time_count"]
    part_time_count = params["part_time_count"]
    full_time_monthly_hours = params["full_time_monthly_hours"]
    part_time_monthly_hours = params["part_time_monthly_hours"]
    full_time_sales_rate = params["full_time_sales_rate"]
    part_time_sales_rate = params["part_time_sales_rate"]
    full_time_wage = params["full_time_wage"]
    part_time_wage = params["part_time_wage"]
    full_time_overtime_pay = params["full_time_overtime_pay"]
    part_time_overtime_pay = params["part_time_overtime_pay"]
    sales_target = params["sales_target"]

    model = pyo.ConcreteModel()

    # Overtime hours (decision variables)
    model.ot_full = pyo.Var(domain=pyo.NonNegativeReals)
    model.ot_part = pyo.Var(domain=pyo.NonNegativeReals)

    # Under-achievement of sales target (deviation variable)
    model.sales_short = pyo.Var(domain=pyo.NonNegativeReals)

    # Sales achieved
    regular_sales = (
        full_time_count * full_time_monthly_hours * full_time_sales_rate
        + part_time_count * part_time_monthly_hours * part_time_sales_rate
    )
    overtime_sales = (
        full_time_count * full_time_sales_rate * model.ot_full
        + part_time_count * part_time_sales_rate * model.ot_part
    )

    # p1: sales target constraint (with under-achievement deviation)
    model.sales_con = pyo.Constraint(
        expr=regular_sales + overtime_sales + model.sales_short >= sales_target
    )

    # Lexicographic goal programming objective:
    # Priority 1: meet sales target (minimize under-achievement)
    # Priority 2: full employment (automatically ensured -> regular hours forced)
    # Priority 3: minimize overtime hours
    # Large weight on sales shortfall; unit weights on overtime hours.
    BIG = 1e6
    model.obj = pyo.Objective(
        expr=BIG * model.sales_short
        + full_time_count * model.ot_full
        + part_time_count * model.ot_part,
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}