import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_stock = params["initial_stock"]
    required_demand = params["required_demand"]
    transport_cost = params["transport_cost"]

    n = len(initial_stock)
    nodes = list(range(n))

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j])

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(transport_cost[i][j] * m.flow[i, j] for (i, j) in m.arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, k):
        return (
            initial_stock[k]
            + sum(m.flow[i, k] for i in nodes if i != k)
            - sum(m.flow[k, j] for j in nodes if j != k)
            >= required_demand[k]
        )

    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}