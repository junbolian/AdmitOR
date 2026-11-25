import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_dests = len(demand)
    origins = range(n_origins)
    dests = range(n_dests)

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=list(origins))
    model.dests = pyo.Set(initialize=list(dests))
    model.routes = pyo.Set(initialize=[(i, j) for i in origins for j in dests], dimen=2)

    model.x = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in origins for j in dests)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in dests) == supply[i]

    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in origins) == demand[j]

    model.demand_con = pyo.Constraint(model.dests, rule=demand_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]

    model.cap_con = pyo.Constraint(model.routes, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}