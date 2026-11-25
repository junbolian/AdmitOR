# IR: {"sets":{"origins":"0..6","destinations":"0..6"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["For each origin i: sum_j shipment[i,j] = supply[i]","For each destination j: sum_i shipment[i,j] = demand[j]"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 6)
    model.destinations = pyo.RangeSet(0, 6)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda instance, i: supply[i],
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda instance, j: demand[j],
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda instance, i, j: cost[i][j],
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(instance, i):
        return sum(
            instance.shipment[i, j] for j in instance.destinations
        ) == instance.supply[i]

    def demand_rule(instance, j):
        return sum(
            instance.shipment[i, j] for i in instance.origins
        ) == instance.demand[j]

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}