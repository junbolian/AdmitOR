import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cost_flat = params["cost"]
    net_out_0 = params["net_outflow_node_0"]
    net_in_7 = params["net_inflow_node_7"]

    N = 8
    nodes = list(range(N))
    nodes_except_0 = [i for i in nodes if i != 0]
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost = {}
    for k, (i, j) in enumerate(arcs):
        cost[(i, j)] = cost_flat[k]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.x[(i, j)] for (i, j) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_0(mdl):
        outflow = sum(mdl.x[(0, j)] for j in nodes if j != 0)
        inflow = sum(mdl.x[(i, 0)] for i in nodes if i != 0)
        return outflow - inflow == net_out_0
    model.balance_start = pyo.Constraint(rule=balance_0)

    def balance_7(mdl):
        inflow = sum(mdl.x[(i, 7)] for i in nodes if i != 7)
        outflow = sum(mdl.x[(7, j)] for j in nodes if j != 7)
        return inflow - outflow == net_in_7
    model.balance_end = pyo.Constraint(rule=balance_7)

    def balance_intermediate_rule(mdl, n):
        inflow = sum(mdl.x[(i, n)] for i in nodes if i != n)
        outflow = sum(mdl.x[(n, j)] for j in nodes if j != n)
        return inflow - outflow == 0
    model.balance_intermediate = pyo.Constraint(nodes_except_0[:-1] + [7][:0] if False else [1, 2, 3, 4, 5, 6], rule=balance_intermediate_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}