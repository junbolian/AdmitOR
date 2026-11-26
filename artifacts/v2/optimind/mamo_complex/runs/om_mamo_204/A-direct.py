import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    n = 8
    source = 0
    sink = 7

    arcs = [(i, j) for i in range(n) for j in range(n)
            if i != j and capacity[i][j] > 0]

    model = pyo.ConcreteModel()
    model.ARC = pyo.Set(initialize=arcs, dimen=2)

    # Drop arcs leaving the sink or entering the source (they can't help)
    active_arcs = [(i, j) for (i, j) in arcs
                   if i != sink and j != source]
    model.FLOWARCS = pyo.Set(initialize=active_arcs, dimen=2)

    model.flow = pyo.Var(model.FLOWARCS, bounds=lambda m, i, j: (0, capacity[i][j]))

    # Conservation for all non-terminal nodes
    def cons_rule(m, k):
        inflow = sum(m.flow[i, j] for (i, j) in active_arcs if j == k)
        outflow = sum(m.flow[i, j] for (i, j) in active_arcs if i == k)
        return inflow == outflow

    intermediate = [k for k in range(n) if k != source and k != sink]
    model.CONS = pyo.Constraint(intermediate, rule=cons_rule)

    def obj_rule(m):
        return sum(m.flow[i, j] for (i, j) in active_arcs if i == source)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}