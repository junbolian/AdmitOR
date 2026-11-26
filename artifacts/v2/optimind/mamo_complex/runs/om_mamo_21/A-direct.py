import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_matrix = params["capacity_matrix"]

    n = len(capacity_matrix)
    source = 0
    sink = n - 1

    arcs = [(i, j) for i in range(n) for j in range(n) if capacity_matrix[i][j] > 0]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.RangeSet(0, n - 1)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def flow_bound_rule(mdl, i, j):
        return mdl.flow[i, j] <= capacity_matrix[i][j]

    model.flow_bound = pyo.Constraint(model.arcs, rule=flow_bound_rule)

    def conservation_rule(mdl, k):
        inflow = sum(mdl.flow[i, k] for i in range(n) if (i, k) in mdl.arcs)
        outflow = sum(mdl.flow[k, j] for j in range(n) if (k, j) in mdl.arcs)
        if k == source:
            return inflow - outflow == -mdl.net_out
        elif k == sink:
            return inflow - outflow == mdl.net_out
        else:
            return inflow - outflow == 0

    model.net_out = pyo.Var(domain=pyo.NonNegativeReals)
    model.conservation = pyo.Constraint(model.nodes, rule=conservation_rule)

    model.obj = pyo.Objective(expr=model.net_out, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}