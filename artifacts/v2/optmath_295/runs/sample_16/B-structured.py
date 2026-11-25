# IR: {"sets":{"I":"0..7","J":"0..7","C":[[0,0],[0,1]]},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","capacity":"params['capacity'][i][j] for (i,j) in C","upper":"capacity[i,j] if (i,j) in C else min(supply[i],demand[j])"},"variables":{"shipment[i,j]":"continuous, 0 <= shipment[i,j] <= upper[i,j]"},"constraints":["sum_j shipment[i,j] = supply[i] for each i","sum_i shipment[i,j] = demand[j] for each j"],"objective":"minimize sum_(i,j) cost[i,j]*shipment[i,j]"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _pair_value(data, origin, destination):
    """Read nested arrays/mappings, tuple-key mappings, or 'i,j' mappings."""
    if isinstance(data, Mapping):
        pair = (origin, destination)
        if pair in data:
            return data[pair]

        string_pair = f"{origin},{destination}"
        if string_pair in data:
            return data[string_pair]

        row = data[origin] if origin in data else data[str(origin)]
    else:
        row = data[origin]

    if isinstance(row, Mapping):
        return row[destination] if destination in row else row[str(destination)]
    return row[destination]


def _indexed_value(data, position):
    """Read an array or a mapping with integer or JSON string keys."""
    if isinstance(data, Mapping):
        return data[position] if position in data else data[str(position)]
    return data[position]


def solve(params):
    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_data = params["cost"]
    capacity_data = params["capacity"]

    origins = range(8)
    destinations = range(8)
    capacitated_pairs = {(0, 0), (0, 1)}

    supplies = {
        origin: _indexed_value(supply_data, origin)
        for origin in origins
    }
    demands = {
        destination: _indexed_value(demand_data, destination)
        for destination in destinations
    }
    costs = {
        (origin, destination): _pair_value(cost_data, origin, destination)
        for origin in origins
        for destination in destinations
    }
    upper_bounds = {
        (origin, destination): (
            _pair_value(capacity_data, origin, destination)
            if (origin, destination) in capacitated_pairs
            else min(supplies[origin], demands[destination])
        )
        for origin in origins
        for destination in destinations
    }

    model = pyo.ConcreteModel()
    model.origins = pyo.Set(initialize=origins, ordered=True)
    model.destinations = pyo.Set(initialize=destinations, ordered=True)

    model.supply = pyo.Param(model.origins, initialize=supplies)
    model.demand = pyo.Param(model.destinations, initialize=demands)
    model.unit_cost = pyo.Param(
        model.origins, model.destinations, initialize=costs
    )
    model.route_upper = pyo.Param(
        model.origins, model.destinations, initialize=upper_bounds
    )

    def shipment_bounds(instance, origin, destination):
        return 0, instance.route_upper[origin, destination]

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
        bounds=shipment_bounds,
    )

    def supply_balance_rule(instance, origin):
        return (
            sum(
                instance.shipment[origin, destination]
                for destination in instance.destinations
            )
            == instance.supply[origin]
        )

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_balance_rule
    )

    def demand_balance_rule(instance, destination):
        return (
            sum(
                instance.shipment[origin, destination]
                for origin in instance.origins
            )
            == instance.demand[destination]
        )

    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin in model.origins
            for destination in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}