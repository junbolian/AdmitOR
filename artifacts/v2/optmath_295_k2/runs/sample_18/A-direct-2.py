import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    num_sources = len(supply)
    num_dests = len(demand)

    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, num_sources - 1)
    model.stores = pyo.RangeSet(0, num_dests - 1)

    model.x = pyo.Var(model.warehouses, model.stores, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.stores) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.warehouses) == demand[j]

    model.supply_constraints = pyo.Constraint(model.warehouses, rule=supply_rule)
    model.demand_constraints = pyo.Constraint(model.stores, rule=demand_rule)

    def obj_rule(mdl):
        return sum(cost_matrix[i][j] * mdl.x[i, j]
                   for i in mdl.warehouses for j in mdl.stores)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}