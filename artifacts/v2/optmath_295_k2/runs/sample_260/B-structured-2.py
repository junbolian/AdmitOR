# {"sets":{"I":"0..10","J":"0..10"},"params":{"supply":"supply[i], i in I","demand":"demand[j], j in J","cost":"cost[i][j], (i,j) in I x J"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(shipment[i,j] for j in J) = supply[i], for each i in I","sum(shipment[i,j] for i in I) = demand[j], for each j in J"],"objective":"minimize sum(cost[i][j] * shipment[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 10)
    model.destinations = pyo.RangeSet(0, 10)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
    )

    model.shipment = pyo.Var(
        model.origins, model.destinations, domain=pyo.NonNegativeReals
    )

    def supply_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.destinations)
            == instance.supply[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.origins)
            == instance.demand[j]
        )

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)

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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}