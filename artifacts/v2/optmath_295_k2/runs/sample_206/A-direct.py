import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_orig - 1)
    model.J = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def ship_cap_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]
    model.ship_cap = pyo.Constraint(model.I, model.J, rule=ship_cap_rule)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J) <= supply[i]
    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) >= demand[j]
    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.I for j in m.J)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}