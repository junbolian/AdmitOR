import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n_warehouses = 12
    n_stores = 14

    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, n_warehouses - 1)
    model.stores = pyo.RangeSet(0, n_stores - 1)

    model.x = pyo.Var(model.warehouses, model.stores, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(transport_cost[i][j] * mdl.x[i, j]
                   for i in mdl.warehouses for j in mdl.stores)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.stores) == supply[i]

    model.supply_constraints = pyo.Constraint(model.warehouses, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.warehouses) == demand[j]

    model.demand_constraints = pyo.Constraint(model.stores, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}