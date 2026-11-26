import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = params["num_cities"]
    source = 0
    sink = N - 1

    arcs = []
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            key = "cap_%d_%d" % (i, j)
            if key in params:
                arcs.append((i, j))

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    def cap_bounds(m, i, j):
        return (0.0, params["cap_%d_%d" % (i, j)])

    model.flow = pyo.Var(model.arcs, bounds=cap_bounds)

    def flow_balance(m, v):
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == v)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == v)
        if v == source:
            return outflow - inflow >= 0
        elif v == sink:
            return inflow - outflow >= 0
        else:
            return outflow - inflow == 0

    model.balance = pyo.Constraint(range(N), rule=flow_balance)

    def obj_expr(m):
        return sum(m.flow[source, j] for (i, j) in arcs if i == source)

    model.obj = pyo.Objective(rule=obj_expr, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}