# IR: {"sets":{"I":[0,1,2,3,4],"J":[0,1,2,3,4]},"params":{"supply":"supply[i]","demand":"demand[j]","cost":"cost[i][j]","capacity":"capacity[i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(shipment[i,j] for j in J) == supply[i] for i in I","sum(shipment[i,j] for i in I) == demand[j] for j in J","shipment[i,j] <= capacity[i][j] for i in I, j in J"],"objective":"minimize sum(cost[i][j] * shipment[i,j] for i in I, j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 4)
    model.destinations = pyo.RangeSet(0, 4)

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
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: sum(
            mdl.shipment[i, j] for j in mdl.destinations
        ) == mdl.supply[i],
    )
    model.demand_balance = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: sum(
            mdl.shipment[i, j] for i in mdl.origins
        ) == mdl.demand[j],
    )
    model.route_capacity = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: (
            mdl.shipment[i, j] <= mdl.capacity[i, j]
        ),
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}