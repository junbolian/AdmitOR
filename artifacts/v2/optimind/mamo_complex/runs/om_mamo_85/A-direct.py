import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.x1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(domain=pyo.NonNegativeReals)

    a1 = params["assembly_hours_type1"]
    a2 = params["assembly_hours_type2"]
    t1 = params["testing_hours_type1"]
    t2 = params["testing_hours_type2"]
    c1 = params["raw_material_cost_type1"]
    c2 = params["raw_material_cost_type2"]
    reg_cap = params["regular_assembly_capacity"]
    test_cap = params["testing_capacity"]
    ot_cap = params["max_overtime_assembly"]
    ot_cost = params["overtime_cost_per_hour"]
    v1 = params["market_value_type1"]
    v2 = params["market_value_type2"]

    # Assembly: regular labor + overtime
    model.assembly_con = pyo.Constraint(
        expr=a1 * model.x1 + a2 * model.x2 <= reg_cap + model.overtime
    )
    # Testing capacity
    model.testing_con = pyo.Constraint(
        expr=t1 * model.x1 + t2 * model.x2 <= test_cap
    )
    # Overtime limit
    model.overtime_con = pyo.Constraint(
        expr=model.overtime <= ot_cap
    )

    # Profit = revenue - raw material cost - overtime cost
    model.profit = pyo.Objective(
        expr=(v1 - c1) * model.x1 + (v2 - c2) * model.x2 - ot_cost * model.overtime,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.profit))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}