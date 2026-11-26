import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables: units of product 1 and 2, and binary for repairs
    model.x1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.rep = pyo.Var(domain=pyo.Binary)

    # Machine capacity constraint (with optional extra hours)
    model.machine_cap = pyo.Constraint(
        expr=params["machine_hours_per_unit_p1"] * model.x1
        + params["machine_hours_per_unit_p2"] * model.x2
        <= params["machine_hours_available"]
        + params["extra_machine_hours"] * model.rep
    )

    # Cash availability constraint
    # Production cost must be financed by available cash + advance on revenues
    model.cash_cap = pyo.Constraint(
        expr=params["production_cost_p1"] * model.x1
        + params["production_cost_p2"] * model.x2
        <= params["available_cash"]
        + params["revenue_advance_rate_p1"] * params["selling_price_p1"] * model.x1
        + params["revenue_advance_rate_p2"] * params["selling_price_p2"] * model.x2
    )

    # Objective: net income = revenue - production cost - repair cost (if repairs done)
    model.obj = pyo.Objective(
        expr=(params["selling_price_p1"] - params["production_cost_p1"]) * model.x1
        + (params["selling_price_p2"] - params["production_cost_p2"]) * model.x2
        - params["repair_cost"] * model.rep,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}