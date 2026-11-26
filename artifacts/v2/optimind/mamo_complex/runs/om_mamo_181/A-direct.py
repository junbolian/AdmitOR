import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    centers = list(range(len(opening_cost)))
    stores = list(range(len(demand)))

    model = pyo.ConcreteModel()

    model.OPEN = pyo.Var(centers, domain=pyo.Binary)
    model.FLOW = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)

    model.capacity_con = pyo.Constraint(
        centers,
        rule=lambda m, c: sum(m.FLOW[c, s] for s in stores) <= capacity[c] * m.OPEN[c],
    )
    model.demand_con = pyo.Constraint(
        stores,
        rule=lambda m, s: sum(m.FLOW[c, s] for c in centers) == demand[s],
    )

    model.obj = pyo.Objective(
        expr=sum(opening_cost[c] * model.OPEN[c] for c in centers)
        + sum(transport_cost[c][s] * model.FLOW[c, s] for c in centers for s in stores),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}