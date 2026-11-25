import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    origins = range(len(supply))
    destinations = range(len(demand))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, destinations, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in destinations) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in origins) == demand[j]

    model.supply_con = pyo.Constraint(origins, rule=supply_rule)
    model.demand_con = pyo.Constraint(destinations, rule=demand_rule)

    def objective_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in origins for j in destinations)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or solver failure"}

    return {"objective": obj_val, "status": "optimal"}