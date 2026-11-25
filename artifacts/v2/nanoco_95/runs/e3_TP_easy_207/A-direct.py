import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hubs = [0, 1, 2]
    areas = [3, 4, 5, 6]

    supply = params["supply"]
    demand = params["demand"]
    capacity = {0: params["capacity_0"], 1: params["capacity_1"], 2: params["capacity_2"]}
    cost = {0: params["cost_0"], 1: params["cost_1"], 2: params["cost_2"]}

    supply_val = {h: supply[i] for i, h in enumerate(hubs)}
    demand_val = {a: demand[i] for i, a in enumerate(areas)}
    cap_val = {(h, a): capacity[h][i] for h in hubs for i, a in enumerate(areas)}
    cost_val = {(h, a): cost[h][i] for h in hubs for i, a in enumerate(areas)}

    model = pyo.ConcreteModel()

    model.hubs = pyo.Set(initialize=hubs, ordered=True)
    model.areas = pyo.Set(initialize=areas, ordered=True)
    model.arcs = pyo.Set(initialize=[(h, a) for h in hubs for a in areas], dimen=2)

    model.flow = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    model.supply_con = pyo.Constraint(
        model.hubs,
        rule=lambda m, h: sum(m.flow[h, a] for a in areas) == supply_val[h],
    )
    model.demand_con = pyo.Constraint(
        model.areas,
        rule=lambda m, a: sum(m.flow[h, a] for h in hubs) == demand_val[a],
    )
    model.capacity_con = pyo.Constraint(
        model.arcs,
        rule=lambda m, h, a: m.flow[h, a] <= cap_val[(h, a)],
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost_val[(h, a)] * model.flow[h, a] for (h, a) in model.arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}