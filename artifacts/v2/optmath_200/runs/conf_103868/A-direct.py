import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(8))
    source = 0
    sink = 7
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def cost(i, j):
        return params["cost_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost(i, j) * m.x[i, j] for (i, j) in m.arcs)
    model.obj_expr = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def flow_rule(m, n):
        out_flow = sum(m.x[n, j] for j in nodes if j != n)
        in_flow = sum(m.x[i, n] for i in nodes if i != n)
        if n == source:
            return out_flow - in_flow == params["net_supply_node_0"]
        elif n == sink:
            return in_flow - out_flow == params["net_demand_node_7"]
        else:
            return in_flow - out_flow == 0
    model.flow_balance = pyo.Constraint(nodes, rule=flow_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj_expr))
    return {"objective": obj_val, "status": "optimal"}