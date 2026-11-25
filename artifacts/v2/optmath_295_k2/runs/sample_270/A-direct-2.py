import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_wh = len(supply)
    n_st = len(demand)

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, n_wh - 1)
    model.S = pyo.RangeSet(0, n_st - 1)

    model.x = pyo.Var(model.W, model.S, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.W for j in m.S)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.S) == supply[i]

    model.supply_con = pyo.Constraint(model.W, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.W) == demand[j]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.cap_con = pyo.Constraint(model.W, model.S, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}