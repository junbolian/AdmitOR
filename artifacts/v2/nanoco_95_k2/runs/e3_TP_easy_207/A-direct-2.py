import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hubs = [0, 1, 2]
    areas = [3, 4, 5, 6]
    arcs = [(i, j) for i in hubs for j in areas]

    supply = {
        0: params["supply_hub0"],
        1: params["supply_hub1"],
        2: params["supply_hub2"],
    }
    demand = {
        3: params["demand_area3"],
        4: params["demand_area4"],
        5: params["demand_area5"],
        6: params["demand_area6"],
    }
    cap = {(i, j): params[f"capacity_arc_{i}_{j}"] for (i, j) in arcs}
    cost = {(i, j): params[f"cost_arc_{i}_{j}"] for (i, j) in arcs}

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.ARC, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    model.cap_con = pyo.Constraint(
        model.ARC,
        rule=lambda mm, i, j: mm.x[(i, j)] <= cap[(i, j)],
    )

    model.supply_con = pyo.Constraint(
        hubs,
        rule=lambda mm, i: sum(mm.x[(i, j)] for j in areas) == supply[i],
    )

    model.demand_con = pyo.Constraint(
        areas,
        rule=lambda mm, j: sum(mm.x[(i, j)] for i in hubs) == demand[j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}