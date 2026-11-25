# IR: {"sets":{"I":"0..10","J":"0..11"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j] or params['cost'][i,j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(shipment[i,j] for j in J) == supply[i] for each i in I","sum(shipment[i,j] for i in I) == demand[j] for each j in J"],"objective":"minimize sum(cost[i,j]*shipment[i,j] for i in I for j in J)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    def transportation_cost(origin, destination):
        if isinstance(cost, Mapping) and (origin, destination) in cost:
            return cost[origin, destination]
        return cost[origin][destination]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 10)
    model.destinations = pyo.RangeSet(0, 11)

    model.supply_units = pyo.Param(
        model.origins,
        initialize=lambda mdl, origin: supply[origin],
        within=pyo.NonNegativeReals,
    )
    model.demand_units = pyo.Param(
        model.destinations,
        initialize=lambda mdl, destination: demand[destination],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, origin, destination: transportation_cost(
            origin, destination
        ),
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    # Equalities enforce the explicit requirement to fully utilize supplies.
    def supply_rule(mdl, origin):
        return (
            sum(
                mdl.shipment[origin, destination]
                for destination in mdl.destinations
            )
            == mdl.supply_units[origin]
        )

    def demand_rule(mdl, destination):
        return (
            sum(
                mdl.shipment[origin, destination]
                for origin in mdl.origins
            )
            == mdl.demand_units[destination]
        )

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin in model.origins
            for destination in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}