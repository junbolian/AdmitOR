import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    dest = len(demand)
    origins = range(n)
    centers = range(dest)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, centers, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(m.x[i, j] * cost[i][j] for i in origins for j in centers)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in centers) == supply[i]

    model.supply_con = pyo.Constraint(origins, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in origins) == demand[j]

    model.demand_con = pyo.Constraint(centers, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}