import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    limit = params["limit"]

    n_fac = len(supply)
    n_cen = len(demand)

    model = pyo.ConcreteModel()

    model.fac = pyo.RangeSet(0, n_fac - 1)
    model.cen = pyo.RangeSet(0, n_cen - 1)

    model.x = pyo.Var(model.fac, model.cen, domain=pyo.NonNegativeReals)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.cen) <= supply[i]

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.fac) == demand[j]

    def limit_rule(m, i, j):
        return m.x[i, j] <= limit[i][j]

    model.supply_con = pyo.Constraint(model.fac, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.cen, rule=demand_rule)
    model.limit_con = pyo.Constraint(model.fac, model.cen, rule=limit_rule)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.fac for j in m.cen)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}