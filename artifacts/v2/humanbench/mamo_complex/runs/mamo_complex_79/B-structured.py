# IR: {"sets":{"warehouses":[1,2,3,4],"routes":"ordered pairs (i,j) with i != j, in lexicographic order"},"params":{"supply":"params['supply']: warehouse mapping or four-element sequence","demand":"params['demand']: warehouse mapping or four-element sequence","transport_cost":"params['transport_cost']: route mapping, twelve-element route sequence, or four-by-four matrix"},"variables":{"shipment[i,j]":"continuous nonnegative"},"constraints":["supply[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i] for every warehouse i"],"objective":"minimize sum(transport_cost[i,j] * shipment[i,j] for (i,j) in routes)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouses = (1, 2, 3, 4)
    routes = tuple(
        (origin, destination)
        for origin in warehouses
        for destination in warehouses
        if origin != destination
    )

    def warehouse_values(data):
        if isinstance(data, Mapping):
            return {
                warehouse: (
                    data[warehouse]
                    if warehouse in data
                    else data[str(warehouse)]
                )
                for warehouse in warehouses
            }

        values = list(data)
        if len(values) != len(warehouses):
            raise ValueError("Expected four warehouse values.")
        return dict(zip(warehouses, values))

    supply_values = warehouse_values(params["supply"])
    demand_values = warehouse_values(params["demand"])

    cost_data = params["transport_cost"]
    if isinstance(cost_data, Mapping):
        cost_values = {
            (origin, destination): cost_data[origin, destination]
            for origin, destination in routes
        }
    else:
        cost_entries = list(cost_data)
        if len(cost_entries) == len(routes):
            cost_values = dict(zip(routes, cost_entries))
        elif len(cost_entries) == len(warehouses):
            cost_rows = [list(row) for row in cost_entries]
            if any(len(row) != len(warehouses) for row in cost_rows):
                raise ValueError("Expected a four-by-four cost matrix.")
            cost_values = {
                (origin, destination): cost_rows[origin - 1][destination - 1]
                for origin, destination in routes
            }
        else:
            raise ValueError("Expected twelve route costs or a four-by-four matrix.")

    model = pyo.ConcreteModel()
    model.warehouses = pyo.Set(initialize=warehouses, ordered=True)
    model.routes = pyo.Set(dimen=2, initialize=routes, ordered=True)

    model.supply = pyo.Param(model.warehouses, initialize=supply_values)
    model.demand = pyo.Param(model.warehouses, initialize=demand_values)
    model.transport_cost = pyo.Param(model.routes, initialize=cost_values)

    model.shipment = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def stock_balance_rule(instance, warehouse):
        incoming = sum(
            instance.shipment[origin, warehouse]
            for origin in instance.warehouses
            if origin != warehouse
        )
        outgoing = sum(
            instance.shipment[warehouse, destination]
            for destination in instance.warehouses
            if destination != warehouse
        )
        return (
            instance.supply[warehouse] + incoming - outgoing
            >= instance.demand[warehouse]
        )

    model.stock_balance = pyo.Constraint(
        model.warehouses, rule=stock_balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}