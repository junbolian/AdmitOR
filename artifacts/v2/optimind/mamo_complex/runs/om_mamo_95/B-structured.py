# IR: {"sets":{"W":[1,2,3,4,5,6],"A":"{(i,j) in W x W: i != j}"},"params":{"supply":"supply[i] from params['supply']","demand":"demand[i] from params['demand']","cost":"cost[i,j] from params['cost_i_j'] for every (i,j) in A"},"variables":{"shipment[i,j]":{"indices":"A","type":"NonNegativeIntegers"}},"constraints":["For each i in W: supply[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i]"],"objective":{"sense":"minimize","expression":"sum(cost[i,j] * shipment[i,j] for (i,j) in A)"}}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Minimize transportation costs while meeting every warehouse's demand.

    Supply and demand may each be:
      - A sequence of six values, ordered by warehouse 1 through 6.
      - A mapping keyed by warehouse numbers 1 through 6, or their strings.

    Shipments may pass through intermediate warehouses. Surplus stock may
    remain at any warehouse.
    """
    warehouses = tuple(range(1, 7))
    arcs = tuple(
        (origin, destination)
        for origin in warehouses
        for destination in warehouses
        if origin != destination
    )

    supply_data = params["supply"]
    demand_data = params["demand"]

    def warehouse_value(data, warehouse):
        if isinstance(data, Mapping):
            if warehouse in data:
                return data[warehouse]
            return data[str(warehouse)]
        return data[warehouse - 1]

    model = pyo.ConcreteModel()
    model.warehouses = pyo.Set(initialize=warehouses, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.supply_units = pyo.Param(
        model.warehouses,
        initialize={
            warehouse: warehouse_value(supply_data, warehouse)
            for warehouse in warehouses
        },
        within=pyo.NonNegativeReals,
    )
    model.demand_units = pyo.Param(
        model.warehouses,
        initialize={
            warehouse: warehouse_value(demand_data, warehouse)
            for warehouse in warehouses
        },
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"cost_{origin}_{destination}"]
            for origin, destination in arcs
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    def demand_balance_rule(current_model, warehouse):
        incoming = sum(
            current_model.shipment[other, warehouse]
            for other in current_model.warehouses
            if other != warehouse
        )
        outgoing = sum(
            current_model.shipment[warehouse, other]
            for other in current_model.warehouses
            if other != warehouse
        )
        return (
            current_model.supply_units[warehouse] + incoming - outgoing
            >= current_model.demand_units[warehouse]
        )

    model.demand_balance = pyo.Constraint(
        model.warehouses, rule=demand_balance_rule
    )

    model.total_transport_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.arcs
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
        obj_val = float(pyo.value(model.total_transport_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}