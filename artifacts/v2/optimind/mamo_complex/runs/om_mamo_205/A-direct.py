import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Build arc list with capacities from params
    arcs = []
    capacities = {}
    for i in range(7):
        for j in range(7):
            if i == j:
                continue
            key = "cap_%d_%d" % (i, j)
            if key in params:
                arcs.append((i, j))
                capacities[(i, j)] = params[key]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    source = 0
    sink = 6
    nodes = range(7)

    def cap_rule(model, i, j):
        return model.flow[i, j] <= capacities[(i, j)]
    model.cap_limit = pyo.Constraint(model.ARCS, rule=cap_rule)

    def conservation_rule(model, k):
        inflow = sum(model.flow[i, k] for (i, j) in arcs if j == k)
        outflow = sum(model.flow[k, j] for (i, j) in arcs if i == k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0
    model.conservation = pyo.Constraint(nodes, rule=conservation_rule)

    def obj_rule(model):
        return sum(model.flow[source, j] for (i, j) in arcs if i == source)
    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_flow))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}