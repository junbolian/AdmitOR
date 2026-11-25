import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cost_matrix = params["cost_matrix"]
    source_supply = params["source_supply"]
    sink_demand = params["sink_demand"]

    n = 7  # structural constant: number of hubs
    nodes = list(range(n))

    model = pyo.ConcreteModel()

    # Arcs are all ordered pairs of distinct nodes
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    # Objective: minimize total transportation cost over used arcs
    model.obj = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize
    )

    # Flow balance constraints
    def balance_rule(m, k):
        outflow = sum(m.x[k, j] for j in nodes if j != k)
        inflow = sum(m.x[i, k] for i in nodes if i != k)
        if k == 0:
            return outflow - inflow == source_supply
        elif k == n - 1:
            return inflow - outflow == sink_demand
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}