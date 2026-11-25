import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, n_orig - 1)
    model.dests = pyo.RangeSet(0, n_dest - 1)

    model.flow = pyo.Var(model.origins, model.dests, domain=pyo.NonNegativeReals)

    model.supply_con = pyo.Constraint(
        model.origins,
        rule=lambda m, i: sum(m.flow[i, j] for j in m.dests) == supply[i],
    )
    model.demand_con = pyo.Constraint(
        model.dests,
        rule=lambda m, j: sum(m.flow[i, j] for i in m.origins) == demand[j],
    )
    model.capacity_con = pyo.Constraint(
        model.origins,
        model.dests,
        rule=lambda m, i, j: m.flow[i, j] <= capacity[i][j],
    )

    model.total_cost = pyo.Objective(
        rule=lambda m: sum(cost[i][j] * m.flow[i, j] for i in m.origins for j in m.dests),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}