# IR: {"sets":{"I":"range(7)","J":"range(6)"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","capacity":"params['capacity'][i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(shipment[i,j] for j in J) <= supply[i] for i in I","sum(shipment[i,j] for i in I) == demand[j] for j in J","shipment[i,j] <= capacity[i,j] for (i,j) in I x J"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve a transportation LP using zero-based sequences and nested matrices."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.Set(initialize=range(7), ordered=True)
    model.destinations = pyo.Set(initialize=range(6), ordered=True)

    model.supply_data = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
        within=pyo.NonNegativeReals,
    )
    model.demand_data = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
        within=pyo.NonNegativeReals,
    )
    model.cost_data = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )
    model.capacity_data = pyo.Param(
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

    def supply_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.destinations)
            <= model.supply_data[i]
        )

    def demand_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.origins)
            == model.demand_data[j]
        )

    def capacity_rule(model, i, j):
        return model.shipment[i, j] <= model.capacity_data[i, j]

    model.supply_limit = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_requirement = pyo.Constraint(
        model.destinations, rule=demand_rule
    )
    model.arc_limit = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_data[i, j] * model.shipment[i, j]
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