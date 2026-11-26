import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = [1, 2, 3, 4, 5]
    arcs = [(1, 2), (1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5),
            (3, 4), (3, 5), (4, 5)]

    cost = {
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 5): params["cost_4_5"],
    }
    supply = {i: params[f"supply_{i}"] for i in locations}
    demand = {i: params[f"demand_{i}"] for i in locations}

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.cost_obj = pyo.Objective(
        expr=sum(cost[a] * model.flow[a] for a in arcs),
        sense=pyo.minimize,
    )

    model.flow_con = pyo.ConstraintList()
    for loc in locations:
        outflow = sum(model.flow[a] for a in arcs if a[0] == loc)
        inflow = sum(model.flow[a] for a in arcs if a[1] == loc)
        # Cars at loc + inflow - outflow = final need (demand)
        model.flow_con.add(supply[loc] + inflow - outflow == demand[loc])

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost_obj))
    return {"objective": obj_val, "status": "optimal"}