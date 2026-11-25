import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    sources = [0, 1, 2]
    sinks = [3, 4, 5, 6]
    arcs = [
        (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 3), (2, 4), (2, 5), (2, 6),
    ]

    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    cap_of = {arcs[k]: capacity[k] for k in range(len(arcs))}
    cost_of = {arcs[k]: cost[k] for k in range(len(arcs))}
    supply_of = {sources[k]: supply[k] for k in range(len(sources))}
    demand_of = {sinks[k]: demand[k] for k in range(len(sinks))}

    model.flow = pyo.Var(arcs, within=pyo.NonNegativeReals)

    model.capacity_con = pyo.Constraint(
        arcs, rule=lambda mm, i, j: mm.flow[(i, j)] <= cap_of[(i, j)]
    )

    model.balance_con = pyo.Constraint(
        sources,
        rule=lambda mm, i: sum(mm.flow[(i, j)] for j in sinks) == supply_of[i],
    )
    model.demand_con = pyo.Constraint(
        sinks,
        rule=lambda mm, j: sum(mm.flow[(i, j)] for i in sources) == demand_of[j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost_of[a] * model.flow[a] for a in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}