# IR: {"sets":{"I":[0,1,2,3,4],"J":[0,1,2,3,4]},"params":{"supply":"I -> nonnegative real","demand":"J -> nonnegative real","cost":"I x J -> real","capacity":"I x J -> nonnegative real"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(shipment[i,j] for j in J) == supply[i] for i in I","sum(shipment[i,j] for i in I) == demand[j] for j in J","shipment[i,j] <= capacity[i,j] for (i,j) in I x J"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _arc_value(data, i, j):
    """Accept a matrix or a mapping indexed by (i, j)."""
    try:
        return data[i, j]
    except (TypeError, KeyError):
        return data[i][j]


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 4)
    model.J = pyo.RangeSet(0, 4)

    model.supply = pyo.Param(
        model.I,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: _arc_value(cost, i, j),
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: _arc_value(capacity, i, j),
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.I, model.J, domain=pyo.NonNegativeReals
    )

    model.supply_balance = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: sum(
            mdl.shipment[i, j] for j in mdl.J
        ) == mdl.supply[i],
    )
    model.demand_balance = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: sum(
            mdl.shipment[i, j] for i in mdl.I
        ) == mdl.demand[j],
    )
    model.arc_capacity = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: (
            mdl.shipment[i, j] <= mdl.capacity[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}