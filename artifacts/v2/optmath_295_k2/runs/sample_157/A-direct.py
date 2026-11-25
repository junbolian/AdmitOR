import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(6))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost = {}
    for i, j in arcs:
        cost[(i, j)] = params[f"cost_{i}_{j}"]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.ARCS, domain=pyo.UnitInterval)

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.flow[(i, j)] for (i, j) in mdl.ARCS)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    supply = {0: params["supply_node0"],
              1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0,
              5: -params["demand_node5"]}

    def balance_rule(mdl, k):
        out_flow = sum(mdl.flow[(k, j)] for j in nodes if j != k)
        in_flow = sum(mdl.flow[(i, k)] for i in nodes if i != k)
        return out_flow - in_flow == supply[k]
    model.balance = pyo.Constraint(model.NODES, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}