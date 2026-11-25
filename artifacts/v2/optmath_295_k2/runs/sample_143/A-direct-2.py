import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_supply = len(supply)
    n_demand = len(demand)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_supply - 1)
    model.J = pyo.RangeSet(0, n_demand - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.I for j in m.J)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J) == supply[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.cap_con = pyo.Constraint(model.I, model.J, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}