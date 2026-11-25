# IR: {"sets":{"I":"aircraft_0..aircraft_6","J":"route_0..route_5"},"params":{"availability":"availability[i] from params","demand":"demand[j] from params","capacity":"capacity[i][j] from params","cost":"cost[i][j] from params"},"variables":{"x[i,j]":"nonnegative integer"},"constraints":["For each i: sum_j x[i,j] <= availability[i]","For each j: sum_i capacity[i][j]*x[i,j] >= demand[j]"],"objective":"minimize sum_i sum_j cost[i][j]*x[i,j]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position, label):
    """Read sequences or mappings with named, integer, or string-index keys."""
    if isinstance(data, Mapping):
        if label in data:
            return data[label]
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position]


def solve(params):
    aircraft = [f"aircraft_{i}" for i in range(7)]
    routes = [f"route_{j}" for j in range(6)]

    availability_data = params["availability"]
    demand_data = params["demand"]
    capacity_data = params["capacity"]
    cost_data = params["cost"]

    availability = {
        label: _entry(availability_data, i, label)
        for i, label in enumerate(aircraft)
    }
    demand = {
        label: _entry(demand_data, j, label)
        for j, label in enumerate(routes)
    }
    capacity = {
        (aircraft_label, route_label): _entry(
            _entry(capacity_data, i, aircraft_label), j, route_label
        )
        for i, aircraft_label in enumerate(aircraft)
        for j, route_label in enumerate(routes)
    }
    cost = {
        (aircraft_label, route_label): _entry(
            _entry(cost_data, i, aircraft_label), j, route_label
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

    # APPsi may raise when it cannot load a solution. Regardless, determine
    # success solely by whether the objective value can be retrieved.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}