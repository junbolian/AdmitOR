import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_destinations = len(demand)
    origins = list(range(n_origins))
    destinations = list(range(n_destinations))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, destinations, domain=pyo.NonNegativeReals)

    def _obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in origins for j in destinations)

    model.total_cost = pyo.Objective(rule=_obj_rule, sense=pyo.minimize)

    def _sup_rule(mdl, i):
        return sum(mdl.x[i, j] for j in destinations) <= supply[i]

    model.supply_cons = pyo.Constraint(origins, rule=_sup_rule)

    def _dem_rule(mdl, j):
        return sum(mdl.x[i, j] for i in origins) >= demand[j]

    model.demand_cons = pyo.Constraint(destinations, rule=_dem_rule)

    def _cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]

    model.cap_cons = pyo.Constraint(origins, destinations, rule=_cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}