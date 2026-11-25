# IR: {"sets":{"I":"range(num_origins)","J":"range(num_destinations)"},"params":{"num_origins":"params['num_origins']","num_destinations":"params['num_destinations']","supply[i]":"params['supply'][i]","demand[j]":"params['demand'][j]","cost[i,j]":"params['cost'][i][j]"},"variables":{"shipment[i,j]":"NonNegativeReals"},"constraints":{"supply_limit[i]":"sum(shipment[i,j] for j in J) <= supply[i]","demand_balance[j]":"sum(shipment[i,j] for i in I) == demand[j]"},"objective":"minimize sum(cost[i,j]*shipment[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_origins = params["num_origins"]
    num_destinations = params["num_destinations"]
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=range(num_origins), ordered=True)
    model.destinations = pyo.Set(
        initialize=range(num_destinations), ordered=True
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

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_limit_rule(mod, i):
        return (
            pyo.quicksum(mod.shipment[i, j] for j in mod.destinations)
            <= mod.supply[i]
        )

    model.supply_limit = pyo.Constraint(
        model.origins, rule=supply_limit_rule
    )

    def demand_balance_rule(mod, j):
        return (
            pyo.quicksum(mod.shipment[i, j] for i in mod.origins)
            == mod.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}