import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 8
    nodes = list(range(N))

    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[(i, j)] = params[f"arc_cost_{i}_{j}"]

    model = pyo.ConcreteModel()
    model.NODES = pyo.Set(initialize=nodes)
    model.ARCS = pyo.Set(initialize=list(cost.keys()), dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in m.ARCS)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def flow_rule(m, k):
        out_flow = sum(m.x[(k, j)] for j in nodes if (k, j) in cost)
        in_flow = sum(m.x[(i, k)] for i in nodes if (i, k) in cost)
        if k == 0:
            return out_flow - in_flow == params["supply_node_0"]
        elif k == N - 1:
            return in_flow - out_flow == params["demand_node_7"]
        else:
            return in_flow - out_flow == 0
    model.flow = pyo.Constraint(model.NODES, rule=flow_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}