import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 9
    source = 0
    sink = 8

    # Build capacity matrix from params
    cap = {}
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            key = f"capacity_{i}_{j}"
            if key in params:
                cap[(i, j)] = params[key]

    arcs = list(cap.keys())

    model = pyo.ConcreteModel()

    model.arc_set = pyo.Set(initialize=arcs, dimen=2)
    model.node_set = pyo.Set(initialize=list(range(N)))

    model.flow = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals)

    def capacity_rule(m, i, j):
        return m.flow[i, j] <= cap[(i, j)]
    model.capacity_con = pyo.Constraint(model.arc_set, rule=capacity_rule)

    def conservation_rule(m, v):
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == v)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == v)
        if v == source:
            return outflow - inflow >= 0
        if v == sink:
            return inflow - outflow >= 0
        return inflow == outflow
    model.conservation_con = pyo.Constraint(model.node_set, rule=conservation_rule)

    def obj_rule(m):
        return sum(m.flow[source, j] for (i, j) in arcs if i == source)
    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_flow))

    return {"objective": obj_val, "status": "optimal"}