# IR: {"sets":{"W":"warehouses 1..6","A":"ordered pairs (i,j) in W x W with i != j and cost[i-1][j-1] not null"},"params":{"supply":"params['supply'], length-6 array","demand":"params['demand'], length-6 array","cost":"params['cost'], 6x6 array"},"variables":{"shipment[i,j]":"nonnegative real for (i,j) in A"},"constraints":["For each i in W: supply[i] + sum(shipment[j,i] for incoming arcs) - sum(shipment[i,j] for outgoing arcs) >= demand[i]."],"objective":"Minimize sum(cost[i,j] * shipment[i,j] for (i,j) in A)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_data = params["cost"]

    warehouses = tuple(range(1, 7))
    arcs = tuple(
        (origin, destination)
        for origin in warehouses
        for destination in warehouses
        if origin != destination
        and cost_data[origin - 1][destination - 1] is not None
    )

    incoming = {
        warehouse: tuple(
            origin
            for origin, destination in arcs
            if destination == warehouse
        )
        for warehouse in warehouses
    }
    outgoing = {
        warehouse: tuple(
            destination
            for origin, destination in arcs
            if origin == warehouse
        )
        for warehouse in warehouses
    }

    model = pyo.ConcreteModel()
    model.W = pyo.Set(initialize=warehouses, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.supply = pyo.Param(
        model.W,
        initialize={
            warehouse: supply_data[warehouse - 1]
            for warehouse in warehouses
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.W,
        initialize={
            warehouse: demand_data[warehouse - 1]
            for warehouse in warehouses
        },
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.A,
        initialize={
            (origin, destination): cost_data[origin - 1][destination - 1]
            for origin, destination in arcs
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def warehouse_balance_rule(instance, warehouse):
        return (
            instance.supply[warehouse]
            + pyo.quicksum(
                instance.shipment[origin, warehouse]
                for origin in incoming[warehouse]
            )
            - pyo.quicksum(
                instance.shipment[warehouse, destination]
                for destination in outgoing[warehouse]
            )
            >= instance.demand[warehouse]
        )

    model.warehouse_balance = pyo.Constraint(
        model.W, rule=warehouse_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.shipping_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}