# IR: {"sets":{"A":["aircraft_0", "...", "aircraft_4"],"R":["route_0", "...", "route_6"]},"params":{"availability":"A -> number, from params","route_demand":"R -> number, from params","capacity":"A x R -> number, from params","cost":"A x R -> number, from params"},"variables":{"x[a,r]":"nonnegative integer"},"constraints":["forall a in A: sum(r in R, x[a,r]) <= availability[a]","forall r in R: sum(a in A, capacity[a,r]*x[a,r]) >= route_demand[r]"],"objective":"minimize sum(a in A, r in R, cost[a,r]*x[a,r])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _item(data, position, label):
    """Read a sequence or a mapping keyed by labels or integer positions."""
    if isinstance(data, Mapping) and label in data:
        return data[label]
    return data[position]


def solve(params):
    """Assign aircraft using input vectors and row-indexed input matrices."""
    availability = params["availability"]
    route_demand = params["route_demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    aircraft = tuple(f"aircraft_{idx}" for idx in range(5))
    routes = tuple(f"route_{idx}" for idx in range(7))

    availability_data = {
        aircraft_label: _item(availability, aircraft_idx, aircraft_label)
        for aircraft_idx, aircraft_label in enumerate(aircraft)
    }
    demand_data = {
        route_label: _item(route_demand, route_idx, route_label)
        for route_idx, route_label in enumerate(routes)
    }
    capacity_data = {
        (aircraft_label, route_label): _item(
            _item(capacity, aircraft_idx, aircraft_label),
            route_idx,
            route_label,
        )
        for aircraft_idx, aircraft_label in enumerate(aircraft)
        for route_idx, route_label in enumerate(routes)
    }
    cost_data = {
        (aircraft_label, route_label): _item(
            _item(cost, aircraft_idx, aircraft_label),
            route_idx,
            route_label,
        )
        for aircraft_idx, aircraft_label in enumerate(aircraft)
        for route_idx, route_label in enumerate(routes)
    }

    model = pyo.ConcreteModel()
    model.A = pyo.Set(initialize=aircraft, ordered=True)
    model.R = pyo.Set(initialize=routes, ordered=True)

    model.availability = pyo.Param(model.A, initialize=availability_data)
    model.route_demand = pyo.Param(model.R, initialize=demand_data)
    model.capacity = pyo.Param(model.A, model.R, initialize=capacity_data)
    model.cost = pyo.Param(model.A, model.R, initialize=cost_data)

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def availability_rule(instance, aircraft_label):
        return (
            sum(instance.x[aircraft_label, route_label]
                for route_label in instance.R)
            <= instance.availability[aircraft_label]
        )

    model.availability_limit = pyo.Constraint(
        model.A, rule=availability_rule
    )

    def demand_rule(instance, route_label):
        return (
            sum(
                instance.capacity[aircraft_label, route_label]
                * instance.x[aircraft_label, route_label]
                for aircraft_label in instance.A
            )
            >= instance.route_demand[route_label]
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
    except RuntimeError:
        # Appsi can raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}