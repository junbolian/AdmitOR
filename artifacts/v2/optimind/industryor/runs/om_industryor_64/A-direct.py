import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.x_high = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_mid = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_low = pyo.Var(domain=pyo.NonNegativeReals)

    model.profit = pyo.Objective(
        expr=params["profit_high"] * model.x_high
        + params["profit_mid"] * model.x_mid
        + params["profit_low"] * model.x_low,
        sense=pyo.maximize,
    )

    model.labor_cap = pyo.Constraint(
        expr=params["labor_high"] * model.x_high
        + params["labor_mid"] * model.x_mid
        + params["labor_low"] * model.x_low
        <= params["labor_capacity"]
    )

    model.inspect_cap = pyo.Constraint(
        expr=params["inspect_high"] * model.x_high
        + params["inspect_mid"] * model.x_mid
        + params["inspect_low"] * model.x_low
        <= params["inspection_capacity"]
    )

    model.demand_high_c = pyo.Constraint(
        expr=model.x_high <= params["demand_high"]
    )
    model.demand_mid_c = pyo.Constraint(
        expr=model.x_mid <= params["demand_mid"]
    )
    model.demand_low_c = pyo.Constraint(
        expr=model.x_low <= params["demand_low"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}