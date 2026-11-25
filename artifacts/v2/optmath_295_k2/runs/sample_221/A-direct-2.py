import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_costs = params["edge_costs"]
    excess_0 = params["node0_outflow_inflow_excess"]
    excess_7 = params["node7_inflow_outflow_excess"]

    n = 8
    edges = [(i, j) for i in range(n) for j in range(n) if i != j]

    cost_map = {}
    k = 0
    for i in range(n):
        for j in range(n):
            if i != j:
                cost_map[(i, j)] = edge_costs[k]
                k += 1

    model = pyo.ConcreteModel()

    model.x = pyo.Var(edges, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_map[(i, j)] * m.x[(i, j)] for (i, j) in edges)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, node):
        outflow = sum(m.x[(node, j)] for j in range(n) if j != node)
        inflow = sum(m.x[(i, node)] for i in range(n) if i != node)
        if node == 0:
            return outflow - inflow == excess_0
        elif node == 7:
            return inflow - outflow == excess_7
        else:
            return outflow - inflow == 0

    model.balance = pyo.Constraint(range(n), rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}