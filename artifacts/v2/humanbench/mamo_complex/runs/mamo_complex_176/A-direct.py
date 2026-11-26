import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Directed edges present in the network (structural: which arcs exist)
    edge_keys = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 5), (2, 6),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5), (3, 6),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    ]

    source = 0
    sink = 6

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=edge_keys, dimen=2)

    def cap_bound(mdl, i, j):
        return params[f"cap_{i}_{j}"]

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.cap = pyo.Constraint(model.arcs, rule=lambda mdl, i, j: mdl.flow[i, j] <= cap_bound(mdl, i, j))

    def conservation_rule(mdl, k):
        outflow = sum(mdl.flow[i, j] for (i, j) in edge_keys if i == k)
        inflow = sum(mdl.flow[i, j] for (i, j) in edge_keys if j == k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return outflow - inflow == 0

    model.conservation = pyo.Constraint(range(7), rule=conservation_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[i, j] for (i, j) in edge_keys if j == sink)

    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}