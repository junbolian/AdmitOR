# {"sets":{"I":"0..6","J":"0..5"},"params":{"supply":"nonnegative vector indexed by I","demand":"nonnegative vector indexed by J","cost":"real matrix indexed by I,J","capacity":"nonnegative matrix indexed by I,J"},"variables":{"shipment[i,j]":"continuous nonnegative"},"constraints":["sum(shipment[i,j] for j in J) <= supply[i] for each i in I","sum(shipment[i,j] for i in I) == demand[j] for each j in J","shipment[i,j] <= capacity[i,j] for each i in I,j in J"],"objective":"minimize sum(cost[i,j]*shipment[i,j] for i in I,j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based sequences for vectors and nested matrix rows."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 6)
    model.destinations = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): capacity[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.destinations)
            <= instance.supply[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.origins)
            == instance.demand[j]
        )

    def capacity_rule(instance, i, j):
        return instance.shipment[i, j] <= instance.capacity[i, j]

    model.supply_limits = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_requirements = pyo.Constraint(
        model.destinations, rule=demand_rule
    )
    model.arc_limits = pyo.Constraint(
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}