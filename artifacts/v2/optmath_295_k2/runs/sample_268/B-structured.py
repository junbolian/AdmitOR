# IR: {"sets":{"O":["origin_0","origin_1","origin_2","origin_3","origin_4"],"D":["destination_0","destination_1","destination_2","destination_3","destination_4","destination_5"]},"params":{"supply":"O -> real","demand":"D -> real","cost":"O x D -> real","capacity":"O x D -> nonnegative real"},"variables":{"ship[o,d]":"nonnegative continuous"},"constraints":["sum(d in D, ship[o,d]) = supply[o] for each o in O","sum(o in O, ship[o,d]) = demand[d] for each d in D","ship[o,d] <= capacity[o,d] for each (o,d) in O x D"],"objective":"minimize sum(o in O, d in D, cost[o,d]*ship[o,d])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _vector_value(data, label, position):
    """Accept a sequence or a mapping keyed by labels or integer positions."""
    if isinstance(data, Mapping):
        if label in data:
            return data[label]
        return data[position]
    return data[position]


def _matrix_value(data, origin, destination, origin_position, destination_position):
    """Accept nested sequences/mappings or mappings keyed by index pairs."""
    if isinstance(data, Mapping):
        if (origin, destination) in data:
            return data[origin, destination]
        if (origin_position, destination_position) in data:
            return data[origin_position, destination_position]
        row = _vector_value(data, origin, origin_position)
    else:
        row = data[origin_position]
    return _vector_value(row, destination, destination_position)


def solve(params):
    origins = [f"origin_{i}" for i in range(5)]
    destinations = [f"destination_{j}" for j in range(6)]

    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_data = params["cost"]
    capacity_data = params["capacity"]

    supply = {
        origin: _vector_value(supply_data, origin, i)
        for i, origin in enumerate(origins)
    }
    demand = {
        destination: _vector_value(demand_data, destination, j)
        for j, destination in enumerate(destinations)
    }
    cost = {
        (origin, destination): _matrix_value(
            cost_data, origin, destination, i, j
        )
        for i, origin in enumerate(origins)
        for j, destination in enumerate(destinations)
    }
    capacity = {
        (origin, destination): _matrix_value(
            capacity_data, origin, destination, i, j
        )
        for i, origin in enumerate(origins)
        for j, destination in enumerate(destinations)
    }

    model = pyo.ConcreteModel()
    model.O = pyo.Set(initialize=origins, ordered=True)
    model.D = pyo.Set(initialize=destinations, ordered=True)

    model.supply = pyo.Param(model.O, initialize=supply, within=pyo.Reals)
    model.demand = pyo.Param(model.D, initialize=demand, within=pyo.Reals)
    model.cost = pyo.Param(model.O, model.D, initialize=cost, within=pyo.Reals)
    model.capacity = pyo.Param(
        model.O, model.D, initialize=capacity, within=pyo.NonNegativeReals
    )

    model.ship = pyo.Var(model.O, model.D, domain=pyo.NonNegativeReals)

    def supply_rule(mod, origin):
        return sum(mod.ship[origin, destination] for destination in mod.D) == (
            mod.supply[origin]
        )

    def demand_rule(mod, destination):
        return sum(mod.ship[origin, destination] for origin in mod.O) == (
            mod.demand[destination]
        )

    def capacity_rule(mod, origin, destination):
        return mod.ship[origin, destination] <= mod.capacity[origin, destination]

    model.supply_balance = pyo.Constraint(model.O, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.D, rule=demand_rule)
    model.route_capacity = pyo.Constraint(model.O, model.D, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination] * model.ship[origin, destination]
            for origin in model.O
            for destination in model.D
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