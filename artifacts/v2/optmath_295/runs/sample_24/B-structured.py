# IR: {"sets":{"I":"0..5","J":"0..5"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","capacity":"params['capacity'][i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(j in J, shipment[i,j]) = supply[i] for each i in I","sum(i in I, shipment[i,j]) = demand[j] for each j in J","shipment[i,j] <= capacity[i,j] for each (i,j) in I x J"],"objective":"minimize sum(i in I, j in J, cost[i,j] * shipment[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 5)
    model.destinations = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: params["supply"][i] for i in model.origins},
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: params["demand"][j] for j in model.destinations},
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.origins
            for j in model.destinations
        },
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): params["capacity"][i][j]
            for i in model.origins
            for j in model.destinations
        },
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
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

    def capacity_rule(instance, i, j):
        return instance.shipment[i, j] <= instance.capacity[i, j]

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)
    model.route_capacity = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}