import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transfer_costs = params["transfer_costs"]

    n = len(supplies)
    regions = list(range(n))
    pairs = [(i, j) for i in regions for j in regions if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(pairs, domain=pyo.NonNegativeReals)

    def _transfer_cost(m):
        return sum(transfer_costs[i][j] * m.x[i, j] for (i, j) in pairs)
    model.transfer_cost = pyo.Expression(rule=_transfer_cost)

    model.balance = pyo.Constraint(
        regions,
        rule=lambda m, j: supplies[j]
        + sum(m.x[i, j] for i in regions if i != j)
        - sum(m.x[j, k] for k in regions if k != j)
        >= demands[j]
    )

    model.obj = pyo.Objective(expr=model.transfer_cost, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}