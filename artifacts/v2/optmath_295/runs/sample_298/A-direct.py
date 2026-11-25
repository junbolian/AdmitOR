import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 10
    nodes = list(range(N))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def _cost(i, j):
        key = f"cost_{i}_{j}"
        if key in params:
            return params[key]
        # Fallback for missing directional cost: use reverse direction if available
        rev = f"cost_{j}_{i}"
        if rev in params:
            return params[rev]
        raise KeyError(key)

    cost = {(i, j): _cost(i, j) for (i, j) in arcs}

    supply = {i: 0.0 for i in nodes}
    supply[0] = params["supply_node0"]
    demand = {i: 0.0 for i in nodes}
    demand[9] = params["demand_node9"]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def flow_rule(m, k):
        out = sum(m.x[(k, j)] for j in nodes if j != k)
        inn = sum(m.x[(i, k)] for i in nodes if i != k)
        return out - inn == supply[k] - demand[k]
    model.flow = pyo.Constraint(nodes, rule=flow_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}