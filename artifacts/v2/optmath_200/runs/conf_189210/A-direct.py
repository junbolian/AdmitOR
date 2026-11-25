import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    n_fact = len(fixed_cost)
    n_month = len(demand)

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, n_fact - 1)
    model.M = pyo.RangeSet(0, n_month - 1)

    model.y = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.x = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(
            fixed_cost[f] * model.y[f, t] + variable_cost[f] * model.x[f, t]
            for f in model.F
            for t in model.M
        ),
        sense=pyo.minimize,
    )

    model.min_prod = pyo.Constraint(
        model.F, model.M,
        rule=lambda m, f, t: m.x[f, t] >= min_production[f] * m.y[f, t],
    )

    model.max_prod = pyo.Constraint(
        model.F, model.M,
        rule=lambda m, f, t: m.x[f, t] <= max_production[f] * m.y[f, t],
    )

    model.demand_sat = pyo.Constraint(
        model.M,
        rule=lambda m, t: sum(m.x[f, t] for f in m.F) >= demand[t],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}