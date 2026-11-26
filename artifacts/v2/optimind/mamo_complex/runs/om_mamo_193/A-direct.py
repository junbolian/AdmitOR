import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_supplies = params["initial_supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    n = len(initial_supplies)
    nodes = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, nodes, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            transport_costs[i][j] * m.x[i, j]
            for i in nodes
            for j in nodes
            if i != j
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, k):
        inflow = sum(m.x[i, k] for i in nodes if i != k)
        outflow = sum(m.x[k, j] for j in nodes if j != k)
        return initial_supplies[k] + inflow - outflow == demands[k]

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}