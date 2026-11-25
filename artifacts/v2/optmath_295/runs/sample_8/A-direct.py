import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    arc_cost = params["arc_cost"]
    supply0 = params["net_outflow_node_0"]
    demand7 = params["net_inflow_node_7"]

    # arc_cost is row-major omitting self-loops: match same ordering
    cost_dict = {}
    k = 0
    for i in nodes:
        for j in nodes:
            if i != j:
                cost_dict[(i, j)] = arc_cost[k]
                k += 1

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)
    model.x = pyo.Var(model.ARCS, within=pyo.Binary)

    def obj_rule(m):
        return sum(cost_dict[a] * m.x[a] for a in m.ARCS)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_flow(m, i):
        return sum(m.x[(i, j)] for j in nodes if j != i)

    def in_flow(m, i):
        return sum(m.x[(j, i)] for j in nodes if j != i)

    model.flow_balance = pyo.ConstraintList()
    for i in nodes:
        if i == 0:
            model.flow_balance.add(out_flow(model, i) - in_flow(model, i) == supply0)
        elif i == 7:
            model.flow_balance.add(in_flow(model, i) - out_flow(model, i) == demand7)
        else:
            model.flow_balance.add(out_flow(model, i) - in_flow(model, i) == 0)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}