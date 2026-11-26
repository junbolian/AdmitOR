import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    regions = list(range(n))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=regions)
    model.J = pyo.Set(initialize=regions)

    # Flow variables: amount shipped from i to j (i -> j), i != j
    model.x = pyo.Var(
        [(i, j) for i in model.I for j in model.J if i != j],
        domain=pyo.NonNegativeReals,
    )

    # Objective: minimize total transportation cost
    model.obj = pyo.Objective(
        expr=sum(
            cost[i][j] * model.x[(i, j)]
            for i in model.I
            for j in model.J
            if i != j
        ),
        sense=pyo.minimize,
    )

    # For each region: supply available (initial) + inflow - outflow >= demand
    def balance_rule(m, i):
        outflow = sum(m.x[(i, j)] for j in m.J if j != i)
        inflow = sum(m.x[(k, i)] for k in m.I if k != i)
        return supply[i] + inflow - outflow >= demand[i]

    model.balance = pyo.Constraint(model.I, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}