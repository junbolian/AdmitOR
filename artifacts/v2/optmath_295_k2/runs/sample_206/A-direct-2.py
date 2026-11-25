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
    model.destinations = pyo.RangeSet(0, n_dest - 1)
    model.links = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(n_orig) for j in range(n_dest)],
    )

    model.flow = pyo.Var(model.links, domain=pyo.NonNegativeReals)

    model.transport_cost = pyo.Objective(
        expr=sum(cost[i][j] * model.flow[i, j] for (i, j) in model.links),
        sense=pyo.minimize,
    )

    model.supply_rule = pyo.Constraint(
        model.origins,
        rule=lambda m, i: sum(m.flow[i, j] for j in range(n_dest)) <= supply[i],
    )
    model.demand_rule = pyo.Constraint(
        model.destinations,
        rule=lambda m, j: sum(m.flow[i, j] for i in range(n_orig)) == demand[j],
    )
    model.capacity_rule = pyo.Constraint(
        model.links,
        rule=lambda m, i, j: m.flow[i, j] <= capacity[i][j],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.transport_cost))
    return {"objective": obj_val, "status": "optimal"}