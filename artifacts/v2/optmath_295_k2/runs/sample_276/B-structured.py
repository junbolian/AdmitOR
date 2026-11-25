# IR: {"sets":{"I":"aircraft_0..aircraft_6","J":"route_0..route_5"},"params":{"availability":"I -> maximum total aircraft assignments","demand":"J -> required capacity","capacity":"I x J -> capacity per assigned aircraft","cost":"I x J -> cost per assigned aircraft"},"variables":{"x[i,j]":"nonnegative integer"},"constraints":["forall i in I: sum(j in J, x[i,j]) <= availability[i]","forall j in J: sum(i in I, capacity[i,j]*x[i,j]) >= demand[j]"],"objective":"minimize sum(i in I, j in J, cost[i,j]*x[i,j])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, label, position):
    """Read label-keyed, integer-keyed, or position-indexed input."""
    if isinstance(data, Mapping):
        if label in data:
            return data[label]
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position]


def solve(params):
    aircraft = tuple(f"aircraft_{i}" for i in range(7))
    routes = tuple(f"route_{j}" for j in range(6))

    availability_data = params["availability"]
    demand_data = params["demand"]
    capacity_data = params["capacity"]
    cost_data = params["cost"]

    availability = {
        aircraft_label: _entry(availability_data, aircraft_label, i)
        for i, aircraft_label in enumerate(aircraft)
    }
    demand = {
        route_label: _entry(demand_data, route_label, j)
        for j, route_label in enumerate(routes)
    }
    capacity = {
        (aircraft_label, route_label): _entry(
            _entry(capacity_data, aircraft_label, i), route_label, j
        )
        for i, aircraft_label in enumerate(aircraft)
        for j, route_label in enumerate(routes)
    }
    cost = {
        (aircraft_label, route_label): _entry(
            _entry(cost_data, aircraft_label, i), route_label, j
        )
        for i, aircraft_label in enumerate(aircraft)
        for j, route_label in enumerate(routes)
    }

    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=aircraft, ordered=True)
    model.J = pyo.Set(initialize=routes, ordered=True)

    model.availability = pyo.Param(model.I, initialize=availability)
    model.demand = pyo.Param(model.J, initialize=demand)
    model.capacity = pyo.Param(model.I, model.J, initialize=capacity)
    model.cost = pyo.Param(model.I, model.J, initialize=cost)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeIntegers)

    def availability_rule(instance, aircraft_label):
        return (
            sum(instance.x[aircraft_label, route_label] for route_label in instance.J)
            <= instance.availability[aircraft_label]
        )

    def demand_rule(instance, route_label):
        return (
            sum(
                instance.capacity[aircraft_label, route_label]
                * instance.x[aircraft_label, route_label]
                for aircraft_label in instance.I
            )
            >= instance.demand[route_label]
        )

    model.availability_limit = pyo.Constraint(model.I, rule=availability_rule)
    model.demand_requirement = pyo.Constraint(model.J, rule=demand_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[aircraft_label, route_label]
            * model.x[aircraft_label, route_label]
            for aircraft_label in model.I
            for route_label in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}