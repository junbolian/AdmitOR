import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_warehouses = len(supply)
    n_stores = len(demand)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_warehouses - 1)
    model.J = pyo.RangeSet(0, n_stores - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J) == supply[i]

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == demand[j]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.I for j in m.J)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}