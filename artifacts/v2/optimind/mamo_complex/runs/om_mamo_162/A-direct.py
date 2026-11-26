import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    D = range(n)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(
        [(i, j) for i in D for j in D if i != j],
        domain=pyo.NonNegativeReals,
    )

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[(i, j)]
                 for i in D for j in D if i != j),
        sense=pyo.minimize,
    )

    def supply_rule(m, i):
        return sum(m.x[(i, j)] for j in D if j != i) <= supply[i]
    model.supply_con = pyo.Constraint(D, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[(i, j)] for i in D if i != j) >= demand[j]
    model.demand_con = pyo.Constraint(D, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}