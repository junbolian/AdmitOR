import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_origins = 14
    n_dests = 14
    origins = list(range(n_origins))
    dests = list(range(n_dests))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, dests, domain=pyo.NonNegativeReals)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in dests) == supply[i]

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in origins) == demand[j]

    model.supply_con = pyo.Constraint(origins, rule=supply_rule)
    model.demand_con = pyo.Constraint(dests, rule=demand_rule)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in origins for j in dests)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}