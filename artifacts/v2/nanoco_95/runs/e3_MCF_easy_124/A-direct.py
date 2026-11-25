import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]

    # Structural definition of the network: (from_node, to_node) in route order
    arcs = [
        (0, 2),  # 1
        (0, 3),  # 2
        (1, 2),  # 3
        (1, 3),  # 4
        (2, 4),  # 5
        (2, 5),  # 6
        (3, 4),  # 7
        (3, 5),  # 8
        (0, 4),  # 9
        (0, 5),  # 10
        (1, 4),  # 11
        (1, 5),  # 12
    ]

    nodes = list(range(6))
    arc_index = list(range(len(arcs)))

    model = pyo.ConcreteModel()

    # Decision variables: flow on each arc (nonnegative)
    model.flow = pyo.Var(arc_index, domain=pyo.NonNegativeReals)

    # Objective: minimize total logistics/spoilage cost
    model.cost = pyo.Objective(
        expr=sum(arc_unit_costs[k] * model.flow[k] for k in arc_index),
        sense=pyo.minimize,
    )

    # Capacity constraints
    model.cap = pyo.Constraint(
        arc_index,
        rule=lambda m, k: m.flow[k] <= arc_capacities[k],
    )

    # Flow conservation: outflow - inflow == supply at each node
    def conservation_rule(m, n):
        outflow = sum(m.flow[k] for k in arc_index if arcs[k][0] == n)
        inflow = sum(m.flow[k] for k in arc_index if arcs[k][1] == n)
        return outflow - inflow == supplies[n]

    model.conservation = pyo.Constraint(nodes, rule=conservation_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}