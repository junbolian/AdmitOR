# IR: {"sets":{"W":"{0,...,6}","A":"{(i,j) in W x W: i != j}"},"params":{"initial_supplies":"W-indexed nonnegative supplies from params","demands":"W-indexed nonnegative demands from params","transport_costs":"directional W x W cost matrix from params"},"variables":{"shipment[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["initial_supplies[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demands[i], for every i in W"],"objective":"minimize sum(transport_costs[i,j] * shipment[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the transportation problem using zero-based input sequences."""
    initial_supplies = params["initial_supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, 6)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.W
            for destination in model.W
            if origin != destination
        ],
    )

    model.supply = pyo.Param(
        model.W,
        initialize={
            warehouse: initial_supplies[warehouse]
            for warehouse in model.W
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.W,
        initialize={
            warehouse: demands[warehouse]
            for warehouse in model.W
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.A,
        initialize={
            (origin, destination): transport_costs[origin][destination]
            for origin, destination in model.A
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def balance_rule(current_model, warehouse):
        incoming = sum(
            current_model.shipment[origin, warehouse]
            for origin in current_model.W
            if origin != warehouse
        )
        outgoing = sum(
            current_model.shipment[warehouse, destination]
            for destination in current_model.W
            if destination != warehouse
        )
        return (
            current_model.supply[warehouse] + incoming - outgoing
            >= current_model.demand[warehouse]
        )

    model.balance = pyo.Constraint(model.W, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Continue to the objective-retrieval test; propagate other errors.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}