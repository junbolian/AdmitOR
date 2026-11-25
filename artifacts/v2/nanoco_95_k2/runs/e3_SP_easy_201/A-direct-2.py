import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_list = [
        (0, 1), (0, 7), (1, 2), (1, 7), (2, 3),
        (2, 6), (3, 4), (3, 5), (3, 8), (3, 9),
        (4, 5), (4, 8), (5, 6), (6, 7), (7, 8),
        (7, 9), (8, 9),
    ]
    nodes = list(range(10))

    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    node_supplies = params["node_supplies"]
    node_coordinates = params["node_coordinates"]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arc_list, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    cost_map = {a: arc_costs[i] for i, a in enumerate(arc_list)}
    cap_map = {a: arc_capacities[i] for i, a in enumerate(arc_list)}
    sup_map = {n: node_supplies[i] for i, n in enumerate(nodes)}

    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def flow_rule(mdl, n):
        inflow = sum(mdl.x[i, j] for (i, j) in arc_list if j == n)
        outflow = sum(mdl.x[i, j] for (i, j) in arc_list if i == n)
        return outflow - inflow == sup_map[n]

    model.flow_con = pyo.Constraint(model.NODES, rule=flow_rule)
    model.cap_con = pyo.Constraint(
        model.ARCS, rule=lambda mdl, i, j: mdl.x[i, j] <= cap_map[(i, j)]
    )

    model.obj = pyo.Objective(
        expr=sum(cost_map[(i, j)] * model.x[i, j] for (i, j) in arc_list),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}