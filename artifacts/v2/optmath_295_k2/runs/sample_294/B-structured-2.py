# IR: {"sets":{"I":"0..14","J":"0..12"},"params":{"supply":"supply[i] from params['supply']","demand":"demand[j] from params['demand']","transport_cost":"transport_cost[i,j] from params['transport_cost'][i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(j in J, shipment[i,j]) = supply[i] for each i in I","sum(i in I, shipment[i,j]) = demand[j] for each j in J"],"objective":"minimize sum(i in I, j in J, transport_cost[i,j] * shipment[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 14)
    model.destinations = pyo.RangeSet(0, 12)

    model.supply_data = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
        within=pyo.Reals,
    )
    model.demand_data = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
        within=pyo.Reals,
    )
    model.cost_data = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.origins, model.destinations, domain=pyo.NonNegativeReals
    )

    def supply_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.destinations)
            == model.supply_data[i]
        )

    def demand_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.origins)
            == model.demand_data[j]
        )

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)

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
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Leave unexpected solver errors visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective unavailable"}

    return {"objective": obj_val, "status": "optimal"}