# IR: {"sets":{"I":"range(params['n_origins'])","J":"range(params['n_destinations'])"},"params":{"n_origins":"frozen index-set size","n_destinations":"frozen index-set size","supply":"nonnegative vector indexed by I","demand":"nonnegative vector indexed by J","cost":"real matrix indexed by I,J","capacity":"nonnegative matrix indexed by I,J"},"variables":{"shipment[i,j]":"continuous nonnegative, i in I, j in J"},"constraints":["sum(shipment[i,j] for j in J) == supply[i] for i in I","sum(shipment[i,j] for i in I) == demand[j] for j in J","shipment[i,j] <= capacity[i,j] for i in I, j in J"],"objective":"minimize sum(cost[i,j]*shipment[i,j] for i in I, j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_origins = params["n_origins"]
    n_destinations = params["n_destinations"]
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=range(n_origins), ordered=True)
    model.destinations = pyo.Set(
        initialize=range(n_destinations), ordered=True
    )

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

    def supply_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.destinations)
            == model.supply[i]
        )

    def demand_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.origins)
            == model.demand[j]
        )

    def capacity_rule(model, i, j):
        return model.shipment[i, j] <= model.capacity[i, j]

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_rule
    )
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}