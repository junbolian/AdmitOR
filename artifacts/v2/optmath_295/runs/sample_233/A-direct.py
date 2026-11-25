import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_producers = params["min_producers"]
    min_delivery = params["min_delivery"]

    n_prod = len(capacity)
    n_cont = len(demand)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_prod - 1)
    model.C = pyo.RangeSet(0, n_cont - 1)

    model.x = pyo.Var(model.P, model.C, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, within=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[p][c] * model.x[p, c] for p in model.P for c in model.C),
        sense=pyo.minimize,
    )

    model.cap_con = pyo.Constraint(
        model.P,
        rule=lambda model, p: sum(model.x[p, c] for c in model.C) <= capacity[p],
    )

    model.demand_con = pyo.Constraint(
        model.C,
        rule=lambda model, c: sum(model.x[p, c] for p in model.P) >= demand[c],
    )

    model.minprod_con = pyo.Constraint(
        model.C,
        rule=lambda model, c: sum(model.y[p, c] for p in model.P) >= min_producers[c],
    )

    model.link_con = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda model, p, c: model.x[p, c] >= min_delivery[p] * model.y[p, c],
    )

    model.bigM_con = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda model, p, c: model.x[p, c] <= capacity[p] * model.y[p, c],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}