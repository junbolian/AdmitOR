import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    contract_min_producers = params["contract_min_producers"]
    producer_min_delivery = params["producer_min_delivery"]
    cost = params["cost"]

    nP = len(producer_capacity)
    nC = len(contract_demand)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, nP - 1)
    model.C = pyo.RangeSet(0, nC - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[p][c] * model.x[p, c] for p in model.P for c in model.C),
        sense=pyo.minimize,
    )

    # capacity
    model.cap = pyo.Constraint(
        model.P,
        rule=lambda m, p: sum(m.x[p, c] for c in m.C) <= producer_capacity[p],
    )

    # demand
    model.dem = pyo.Constraint(
        model.C,
        rule=lambda m, c: sum(m.x[p, c] for p in m.P) >= contract_demand[c],
    )

    # min producers
    model.minprod = pyo.Constraint(
        model.C,
        rule=lambda m, c: sum(m.y[p, c] for p in m.P) >= contract_min_producers[c],
    )

    # linking + minimum delivery
    def link_rule(m, p, c):
        return m.x[p, c] >= producer_min_delivery[p] * m.y[p, c]

    model.link = pyo.Constraint(model.P, model.C, rule=link_rule)

    def ub_rule(m, p, c):
        big = max(contract_demand[c], producer_capacity[p])
        return m.x[p, c] <= big * m.y[p, c]

    model.ub = pyo.Constraint(model.P, model.C, rule=ub_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}

    return {"objective": obj_val, "status": "optimal"}