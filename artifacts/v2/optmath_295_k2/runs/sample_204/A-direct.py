import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    cost = params["cost"]
    capacity = params["capacity"]

    n = len(supply)
    # Structural index sets (nodes / arcs)
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()

    # Flow variables on each route, bounded by route capacity
    model.x = pyo.Var(arcs, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, capacity[i][j]))

    # Objective: total transportation cost
    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Flow balance: net outflow - inflow must equal each city's surplus (net supply)
    def balance_rule(m, k):
        return sum(m.x[k, j] for j in range(n) if j != k) - \
               sum(m.x[i, k] for i in range(n) if i != k) == supply[k]

    model.balance = pyo.Constraint(range(n), rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}