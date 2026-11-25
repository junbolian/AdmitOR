import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    costs = params["costs"]

    n_warehouses = len(supplies)
    n_stores = len(demands)

    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, n_warehouses - 1)
    model.stores = pyo.RangeSet(0, n_stores - 1)

    model.ship = pyo.Var(model.warehouses, model.stores, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.ship[i, j] for j in mdl.stores) == supplies[i]
    model.supply_con = pyo.Constraint(model.warehouses, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.ship[i, j] for i in mdl.warehouses) == demands[j]
    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def obj_rule(mdl):
        return sum(costs[i][j] * mdl.ship[i, j]
                   for i in mdl.warehouses for j in mdl.stores)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}