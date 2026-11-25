# IR: {"sets":{"I":"0..11","J":"0..9"},"params":{"transport_cost":"real[I,J], read from params['transport_cost'][i][j]","supply":"nonnegative real[I], read from params['supply'][i]","demand":"nonnegative real[J], read from params['demand'][j]"},"variables":{"shipment[i,j]":"continuous, nonnegative"},"constraints":["sum(shipment[i,j] for j in J) == supply[i] for each i in I","sum(shipment[i,j] for i in I) == demand[j] for each j in J"],"objective":"minimize sum(transport_cost[i,j] * shipment[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    transport_cost = params["transport_cost"]
    supply = params["supply"]
    demand = params["demand"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 11)
    model.destinations = pyo.RangeSet(0, 9)

    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: transport_cost[i][j],
        within=pyo.Reals,
    )
    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.destinations)
            == mdl.supply[i]
        )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.origins)
            == mdl.demand[j]
        )

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
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