import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(6))
    source, sink = 0, 5

    # Build arcs only where a capacity key exists in params.
    arc_list = []
    capacity = {}
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            key = "capacity_%d_%d" % (i, j)
            if key in params:
                cap = params[key]
                arc_list.append((i, j))
                capacity[(i, j)] = cap

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arc_list, dimen=2)

    def flow_bounds(mdl, i, j):
        return (0, capacity[(i, j)])

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals, bounds=flow_bounds)

    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    def conservation_rule(mdl, k):
        inflow = sum(mdl.flow[i, k] for (i, j) in arc_list if j == k)
        outflow = sum(mdl.flow[k, j] for (i, j) in arc_list if i == k)
        if k == source:
            return outflow - inflow == mdl.total_flow
        elif k == sink:
            return inflow - outflow == mdl.total_flow
        else:
            return inflow - outflow == 0

    model.FLOW = pyo.Constraint(nodes, rule=conservation_rule)

    model.objective = pyo.Objective(expr=model.total_flow, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}