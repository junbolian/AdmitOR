import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    cities = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(cities, cities, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in cities for j in cities if i != j)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) <= supply[i]

    model.supply_con = pyo.Constraint(cities, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == demand[j]

    model.demand_con = pyo.Constraint(cities, rule=demand_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}

    return {"objective": obj_val, "status": "optimal"}