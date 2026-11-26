import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = [0, 1, 2, 3, 4, 5, 6]
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 0), (1, 4), (1, 5), (1, 6),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5), (2, 6),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5), (3, 6),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
        (5, 0), (5, 2), (5, 3), (5, 4), (5, 6),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    ]
    source = 0
    sink = 6

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    def cap_rule(mdl, i, j):
        return float(params["cap_%d_%d" % (i, j)])

    model.capacity = pyo.Param(model.arcs, initialize=cap_rule, within=pyo.NonNegativeReals)
    model.flow = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    def flow_bound(mdl, i, j):
        return mdl.flow[i, j] <= mdl.capacity[i, j]

    model.flow_bound_con = pyo.Constraint(model.arcs, rule=flow_bound)

    def conservation(mdl, k):
        if k == source:
            return sum(mdl.flow[i, j] for (i, j) in arcs if i == k) - \
                   sum(mdl.flow[i, j] for (i, j) in arcs if j == k) == \
                   sum(mdl.flow[i, j] for (i, j) in arcs if i == k)  # placeholder replaced below
        return pyo.Constraint.Skip

    # Build conservation explicitly
    def cons_rule(mdl, k):
        outflow = sum(mdl.flow[i, j] for (i, j) in mdl.arcs if i == k)
        inflow = sum(mdl.flow[i, j] for (i, j) in mdl.arcs if j == k)
        if k == source:
            return outflow - inflow == mdl.net_out
        elif k == sink:
            return inflow - outflow == mdl.net_out
        else:
            return outflow - inflow == 0

    model.net_out = pyo.Var(within=pyo.NonNegativeReals)
    model.nodes = pyo.Set(initialize=nodes)
    model.conservation_con = pyo.Constraint(model.nodes, rule=cons_rule)

    model.obj = pyo.Objective(expr=model.net_out, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}