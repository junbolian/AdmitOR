import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_warehouses = len(supply)
    n_stores = len(demand)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_warehouses - 1)
    model.J = pyo.RangeSet(0, n_stores - 1)

    def cap_rule(mdl, i, j):
        return (0, capacity[i][j])

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals, bounds=cap_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.I for j in mdl.J)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) == supply[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.I) == demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}