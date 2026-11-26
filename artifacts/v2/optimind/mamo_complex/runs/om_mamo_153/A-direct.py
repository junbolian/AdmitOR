import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    nodes = list(range(6))
    source = 0
    sink = 5

    # Directed edges (only those with positive capacity listed)
    edge_list = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4),
        (3, 0), (3, 1), (3, 2), (3, 4),
        (4, 0), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    ]

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.EDGES = pyo.Set(initialize=edge_list, dimen=2)

    # Capacity from params
    cap_data = {}
    for (i, j) in edge_list:
        cap_data[(i, j)] = float(params[f"capacity_{i}_{j}"])
    model.capacity = pyo.Param(model.EDGES, initialize=cap_data, mutable=False)

    # Flow variables
    model.flow = pyo.Var(model.EDGES, domain=pyo.NonNegativeReals)

    # Capacity constraints
    def cap_rule(m, i, j):
        return m.flow[i, j] <= m.capacity[i, j]
    model.cap_con = pyo.Constraint(model.EDGES, rule=cap_rule)

    # Flow conservation
    def conservation_rule(m, n):
        outflow = sum(m.flow[i, j] for (i, j) in edge_list if i == n)
        inflow = sum(m.flow[i, j] for (i, j) in edge_list if j == n)
        if n == source:
            return outflow - inflow >= 0
        elif n == sink:
            return inflow - outflow >= 0
        else:
            return outflow - inflow == 0
    model.flow_con = pyo.Constraint(model.NODES, rule=conservation_rule)

    # Objective: maximize flow out of source (equivalently into sink)
    def obj_rule(m):
        return sum(m.flow[source, j] for j in nodes if (source, j) in edge_list)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}