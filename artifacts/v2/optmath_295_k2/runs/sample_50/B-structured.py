# IR: {"sets":{"A":["aircraft_0","aircraft_1","aircraft_2","aircraft_3","aircraft_4"],"R":["route_0","route_1","route_2","route_3","route_4","route_5","route_6"]},"params":{"availability":"nonnegative[A], read from params","route_demand":"nonnegative[R], read from params","capacity":"nonnegative[A,R], read from params","cost":"real[A,R], read from params"},"variables":{"x[A,R]":"nonnegative integer"},"constraints":["For each a in A: sum(x[a,r] for r in R) <= availability[a]","For each r in R: sum(capacity[a,r]*x[a,r] for a in A) >= route_demand[r]"],"objective":"minimize sum(cost[a,r]*x[a,r] for a in A for r in R)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position, label):
    """Accept positional sequences or mappings keyed by labels or integers."""
    if isinstance(data, Mapping):
        return data[label] if label in data else data[position]
    return data[position]


def solve(params):
    availability_data = params["availability"]
    demand_data = params["route_demand"]
    capacity_data = params["capacity"]
    cost_data = params["cost"]

    aircraft = tuple(f"aircraft_{idx}" for idx in range(5))
    routes = tuple(f"route_{idx}" for idx in range(7))

    availability = {
        aircraft_label: _entry(availability_data, aircraft_idx, aircraft_label)
        for aircraft_idx, aircraft_label in enumerate(aircraft)
    }
    route_demand = {
        route_label: _entry(demand_data, route_idx, route_label)
        for route_idx, route_label in enumerate(routes)
    }
    capacity = {
        (aircraft_label, route_label): _entry(
            _entry(capacity_data, aircraft_idx, aircraft_label),
            route_idx,
            route_label,
        )
        for aircraft_idx, aircraft_label in enumerate(aircraft)
        for route_idx, route_label in enumerate(routes)
    }
    cost = {
        (aircraft_label, route_label): _entry(
            _entry(cost_data, aircraft_idx, aircraft_label),
            route_idx,
            route_label,
        )
        for aircraft_idx, aircraft_label in enumerate(aircraft)
        for route_idx, route_label in enumerate(routes)
    }

    model = pyo.ConcreteModel()
    model.A = pyo.Set(initialize=aircraft, ordered=True)
    model.R = pyo.Set(initialize=routes, ordered=True)

    model.availability = pyo.Param(
        model.A, initialize=availability, within=pyo.NonNegativeReals
    )
    model.route_demand = pyo.Param(
        model.R, initialize=route_demand, within=pyo.NonNegativeReals
    )
    model.capacity = pyo.Param(
        model.A, model.R, initialize=capacity, within=pyo.NonNegativeReals
    )
    model.cost = pyo.Param(
        model.A, model.R, initialize=cost, within=pyo.Reals
    )

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def availability_rule(block, aircraft_label):
        return (
            sum(block.x[aircraft_label, route_label] for route_label in block.R)
            <= block.availability[aircraft_label]
        )

    model.availability_limit = pyo.Constraint(
        model.A, rule=availability_rule
    )

    def demand_rule(block, route_label):
        return (
            sum(
                block.capacity[aircraft_label, route_label]
                * block.x[aircraft_label, route_label]
                for aircraft_label in block.A
            )
            >= block.route_demand[route_label]
        )

    model.demand_requirement = pyo.Constraint(model.R, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[aircraft_label, route_label]
            * model.x[aircraft_label, route_label]
            for aircraft_label in model.A
            for route_label in model.R
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except (RuntimeError, ValueError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}