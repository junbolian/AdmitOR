# IR: {"sets":{"W":"0,...,6","A":"ordered (i,j) with i != j","P":"(i,j) with i < j, row-major"},"params":{"supplies":"params['supplies'][i]","demands":"params['demands'][i]","transport_costs":"params['transport_costs']: 21 scalars in P order apply to both directions; 21 two-entry sequences in P order specify [i->j,j->i]; alternatively 42 row-major off-diagonal scalars, a 7x7 matrix, or 7x6 off-diagonal rows"},"variables":{"shipment[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["supplies[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demands[i] for i in W"],"objective":"minimize sum(transport_costs[i,j] * shipment[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    warehouses = tuple(range(7))
    arcs = tuple(
        (origin, destination)
        for origin in warehouses
        for destination in warehouses
        if origin != destination
    )
    pairs = tuple(
        (origin, destination)
        for origin in warehouses
        for destination in warehouses
        if origin < destination
    )

    if len(supplies) != len(warehouses):
        return {"objective": None, "status": "invalid_supplies"}
    if len(demands) != len(warehouses):
        return {"objective": None, "status": "invalid_demands"}

    directed_costs = {}

    if len(transport_costs) == len(pairs):
        for position, (origin, destination) in enumerate(pairs):
            entry = transport_costs[position]
            if hasattr(entry, "__len__") and not isinstance(entry, (str, bytes)):
                if len(entry) != 2:
                    return {"objective": None, "status": "invalid_cost_pair"}
                directed_costs[origin, destination] = entry[0]
                directed_costs[destination, origin] = entry[1]
            else:
                # A scalar upper-triangle entry supplies both directions.
                directed_costs[origin, destination] = entry
                directed_costs[destination, origin] = entry

    elif len(transport_costs) == len(arcs):
        directed_costs = dict(zip(arcs, transport_costs))

    elif len(transport_costs) == len(warehouses):
        if any(
            not hasattr(row, "__len__") or isinstance(row, (str, bytes))
            for row in transport_costs
        ):
            return {"objective": None, "status": "invalid_cost_rows"}

        row_lengths = tuple(len(row) for row in transport_costs)

        if all(length == len(warehouses) for length in row_lengths):
            directed_costs = {
                (origin, destination): transport_costs[origin][destination]
                for origin, destination in arcs
            }
        elif all(length == len(warehouses) - 1 for length in row_lengths):
            for origin in warehouses:
                destinations = tuple(
                    destination
                    for destination in warehouses
                    if destination != origin
                )
                for position, destination in enumerate(destinations):
                    directed_costs[origin, destination] = (
                        transport_costs[origin][position]
                    )
        else:
            return {"objective": None, "status": "invalid_cost_rows"}

    else:
        return {"objective": None, "status": "invalid_cost_dimensions"}

    model = pyo.ConcreteModel()
    model.warehouses = pyo.Set(initialize=warehouses, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.initial_supply = pyo.Param(
        model.warehouses,
        initialize={
            warehouse: supplies[warehouse] for warehouse in warehouses
        },
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.warehouses,
        initialize={
            warehouse: demands[warehouse] for warehouse in warehouses
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize=directed_costs,
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    def demand_balance_rule(instance, warehouse):
        incoming = sum(
            instance.shipment[other, warehouse]
            for other in instance.warehouses
            if other != warehouse
        )
        outgoing = sum(
            instance.shipment[warehouse, other]
            for other in instance.warehouses
            if other != warehouse
        )
        return (
            instance.initial_supply[warehouse] + incoming - outgoing
            >= instance.required_demand[warehouse]
        )

    model.demand_balance = pyo.Constraint(
        model.warehouses,
        rule=demand_balance_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.arcs
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