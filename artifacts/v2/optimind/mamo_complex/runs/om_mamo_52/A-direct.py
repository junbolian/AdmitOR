import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.x1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(domain=pyo.NonNegativeReals)

    a1 = params["assembly_hours_product1"]
    t1 = params["testing_hours_product1"]
    m1 = params["material_cost_product1"]
    a2 = params["assembly_hours_product2"]
    t2 = params["testing_hours_product2"]
    m2 = params["material_cost_product2"]
    reg_cap = params["regular_assembly_capacity"]
    test_cap = params["testing_capacity"]
    ot_cap = params["overtime_assembly_capacity"]
    ot_cost = params["overtime_cost_per_hour"]
    v1 = params["market_value_product1"]
    v2 = params["market_value_product2"]

    model.assembly_limit = pyo.Constraint(
        expr=a1 * model.x1 + a2 * model.x2 <= reg_cap + model.overtime
    )
    model.testing_limit = pyo.Constraint(
        expr=t1 * model.x1 + t2 * model.x2 <= test_cap
    )
    model.overtime_limit = pyo.Constraint(expr=model.overtime <= ot_cap)

    model.profit = pyo.Objective(
        expr=(v1 - m1) * model.x1
        + (v2 - m2) * model.x2
        - ot_cost * model.overtime,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.profit))
    except Exception:
        return {"objective": None, "status": "infeasible or solve failed"}

    return {"objective": obj_val, "status": "optimal"}