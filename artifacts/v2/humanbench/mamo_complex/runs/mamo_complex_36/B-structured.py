# IR: {"sets":{"R":[1,2,3,4,5,6],"A":"{(i,j) in R x R: i != j}"},"params":{"supply":"six-element sequence; supply[i-1]","demand":"six-element sequence; demand[i-1]","transport_cost":"6x6 sequence; transport_cost[i-1][j-1]"},"variables":{"shipment[i,j]":"NonNegativeReals for (i,j) in A; transshipment permitted"},"constraints":["For each i in R: supply[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i]"],"objective":"Minimize sum(transport_cost[i,j] * shipment[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(1, 6)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.regions
            for j in model.regions
            if i != j
        ],
    )

    model.initial_supply = pyo.Param(
        model.regions,
        initialize=lambda _, i: supply[i - 1],
    )
    model.required_food = pyo.Param(
        model.regions,
        initialize=lambda _, i: demand[i - 1],
    )
    model.shipping_cost = pyo.Param(
        model.routes,
        initialize=lambda _, i, j: transport_cost[i - 1][j - 1],
    )

    model.shipment = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def food_balance_rule(instance, i):
        incoming = sum(
            instance.shipment[j, i]
            for j in instance.regions
            if j != i
        )
        outgoing = sum(
            instance.shipment[i, j]
            for j in instance.regions
            if j != i
        )
        return (
            instance.initial_supply[i] + incoming - outgoing
            >= instance.required_food[i]
        )

    model.food_balance = pyo.Constraint(
        model.regions, rule=food_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.shipping_cost[i, j] * model.shipment[i, j]
            for i, j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}