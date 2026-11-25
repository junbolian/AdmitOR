import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_cost = params["edge_cost"]
    supply_node_0 = params["supply_node_0"]
    demand_node_7 = params["demand_node_7"]

    n = 8
    nodes = list(range(n))

    # Build ordered arc list (i, j), i != j, row-major
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost = {}
    for k, (i, j) in enumerate(arcs):
        cost[(i, j)] = edge_cost[k]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    # Flow balance: outflow - inflow = supply (supply>0), demand (<0), else 0
    def balance_rule(m, k):
        outflow = sum(m.x[k, j] for j in nodes if j != k)
        inflow = sum(m.x[i, k] for i in nodes if i != k)
        if k == 0:
            return outflow - inflow == supply_node_0
        elif k == 7:
            return outflow - inflow == -demand_node_7
        else:
            return outflow - inflow == 0

    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def obj_rule(m):
        return sum(cost[a] * m.x[a] for a in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}