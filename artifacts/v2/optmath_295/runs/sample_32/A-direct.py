import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n = len(supply)
    m = len(demand)
    origins = list(range(n))
    dests = list(range(m))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, dests, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in origins for j in dests)

    model.transport_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in dests) == supply[i]

    model.supply_constraint = pyo.Constraint(origins, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in origins) == demand[j]

    model.demand_constraint = pyo.Constraint(dests, rule=demand_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]

    model.capacity_constraint = pyo.Constraint(origins, dests, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.transport_cost))
    return {"objective": obj_val, "status": "optimal"}