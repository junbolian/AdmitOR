import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    demands = params["demands"]
    shipping_costs = params["shipping_costs"]
    capacities = params["capacities"]

    n_fac = len(fixed_costs)
    n_cust = len(demands)

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, n_fac - 1)
    model.C = pyo.RangeSet(0, n_cust - 1)

    model.y = pyo.Var(model.F, within=pyo.Binary)
    model.x = pyo.Var(model.F, model.C, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(fixed_costs[f] * model.y[f] for f in model.F)
        + sum(shipping_costs[f][c] * model.x[f, c] for f in model.F for c in model.C),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        model.C,
        rule=lambda m, c: sum(m.x[f, c] for f in m.F) == demands[c],
    )

    model.cap_con = pyo.Constraint(
        model.F,
        rule=lambda m, f: sum(m.x[f, c] for c in m.C) <= capacities[f] * m.y[f],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}