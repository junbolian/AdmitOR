import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    transport_capacity = params["transport_capacity"]

    n_origins = len(supply)
    n_destinations = len(demand)
    n_products = len(supply[0])

    model = pyo.ConcreteModel()

    model.ORI = pyo.RangeSet(0, n_origins - 1)
    model.DEST = pyo.RangeSet(0, n_destinations - 1)
    model.PROD = pyo.RangeSet(0, n_products - 1)

    model.x = pyo.Var(model.ORI, model.DEST, model.PROD, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            cost[i][j][k] * mdl.x[i, j, k]
            for i in mdl.ORI
            for j in mdl.DEST
            for k in mdl.PROD
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i, k):
        return sum(mdl.x[i, j, k] for j in mdl.DEST) <= supply[i][k]

    model.supply_constraint = pyo.Constraint(model.ORI, model.PROD, rule=supply_rule)

    def demand_rule(mdl, j, k):
        return sum(mdl.x[i, j, k] for i in mdl.ORI) >= demand[j][k]

    model.demand_constraint = pyo.Constraint(model.DEST, model.PROD, rule=demand_rule)

    def capacity_rule(mdl, i, j):
        return sum(mdl.x[i, j, k] for k in mdl.PROD) <= transport_capacity[i][j]

    model.capacity_constraint = pyo.Constraint(model.ORI, model.DEST, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}