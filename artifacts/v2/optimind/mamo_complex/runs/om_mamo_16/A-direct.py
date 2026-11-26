import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    nodes = list(range(n))

    model = pyo.ConcreteModel()
    model.IDX = pyo.Set(initialize=nodes)
    model.PAIRS = pyo.Set(dimen=2, initialize=[(a, b) for a in nodes for b in nodes if a != b])

    model.x = pyo.Var(model.PAIRS, domain=pyo.NonNegativeReals)

    def balance_rule(mdl, i):
        outflow = sum(mdl.x[i, j] for j in nodes if j != i)
        inflow = sum(mdl.x[j, i] for j in nodes if j != i)
        return supply[i] - outflow + inflow >= demand[i]

    model.balance = pyo.Constraint(model.IDX, rule=balance_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[a][b] * model.x[a, b] for (a, b) in model.PAIRS),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}