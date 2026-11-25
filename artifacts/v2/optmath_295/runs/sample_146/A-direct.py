import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    origins = list(range(len(supply)))
    destinations = list(range(len(demand)))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, destinations, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in origins for j in destinations)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.supply_con = pyo.Constraint(
        origins,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in destinations) == supply[i],
    )

    model.demand_con = pyo.Constraint(
        destinations,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in origins) == demand[j],
    )

    model.capacity_con = pyo.Constraint(
        origins,
        destinations,
        rule=lambda mdl, i, j: mdl.x[i, j] <= capacity[i][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}