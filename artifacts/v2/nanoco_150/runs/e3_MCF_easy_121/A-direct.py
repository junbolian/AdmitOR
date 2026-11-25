import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    coordinates = params["coordinates"]
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]

    arcs = [
        (0, 2), (0, 3), (1, 2), (1, 3),
        (2, 4), (2, 5), (3, 4), (3, 5),
        (0, 4), (0, 5), (1, 4), (1, 5),
    ]
    nodes = list(range(6))

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    model.capacity = pyo.Constraint(
        model.arcs,
        rule=lambda m, i, j: m.flow[i, j] <= arc_capacities[arcs.index((i, j))],
    )

    cost_map = {arcs[k]: arc_costs[k] for k in range(len(arcs))}

    def flow_balance(m, n):
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == n)
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == n)
        return outflow - inflow == supplies[n]

    model.balance = pyo.Constraint(model.nodes, rule=flow_balance)

    model.total_cost = pyo.Objective(
        expr=sum(cost_map[(i, j)] * model.flow[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}