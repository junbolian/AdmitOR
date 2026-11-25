import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_warehouses = 6
    n_stores = 6

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, n_warehouses - 1)
    model.S = pyo.RangeSet(0, n_stores - 1)

    model.x = pyo.Var(model.W, model.S, domain=pyo.NonNegativeReals)

    def supply_rule(mdl_c, i):
        return sum(mdl_c.x[i, j] for j in mdl_c.S) == supply[i]

    def demand_rule(mdl_c, j):
        return sum(mdl_c.x[i, j] for i in mdl_c.W) == demand[j]

    model.supply_con = pyo.Constraint(model.W, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def objective_rule(mdl_c):
        return sum(cost[i][j] * mdl_c.x[i, j] for i in mdl_c.W for j in mdl_c.S)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}