# IR: {"sets":{"A":["aircraft_0","aircraft_1","aircraft_2","aircraft_3","aircraft_4","aircraft_5"],"R":["route_0","route_1","route_2","route_3"]},"params":{"availability":"A -> real","demand":"R -> real","capability":"A x R -> real","cost":"A x R -> real"},"variables":{"x[a,r]":"nonnegative integer"},"constraints":["sum(x[a,r] for r in R) <= availability[a] for a in A","sum(capability[a,r]*x[a,r] for a in A) >= demand[r] for r in R"],"objective":"minimize sum(cost[a,r]*x[a,r] for a in A for r in R)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position, label):
    """Accept a sequence or a mapping keyed by labels or integer indices."""
    if isinstance(data, Mapping):
        if label in data:
            return data[label]
        return data[position]
    return data[position]


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capability = params["capability"]
    cost = params["cost"]

    aircraft = tuple(f"aircraft_{idx}" for idx in range(6))
    routes = tuple(f"route_{idx}" for idx in range(4))

    availability_data = {
        aircraft_label: _entry(availability, aircraft_idx, aircraft_label)
        for aircraft_idx, aircraft_label in enumerate(aircraft)
    }
    demand_data = {
        route_label: _entry(demand, route_idx, route_label)
        for route_idx, route_label in enumerate(routes)
    }
    capability_data = {
        (aircraft_label, route_label): _entry(
            _entry(capability, aircraft_idx, aircraft_label),
            route_idx,
            route_label,
        )
        for aircraft_idx, aircraft_label in enumerate(aircraft)
        for route_idx, route_label in enumerate(routes)
    }
    cost_data = {
        (aircraft_label, route_label): _entry(
            _entry(cost, aircraft_idx, aircraft_label),
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
        model.A, initialize=availability_data, within=pyo.Reals
    )
    model.demand = pyo.Param(
        model.R, initialize=demand_data, within=pyo.Reals
    )
    model.capability = pyo.Param(
        model.A, model.R, initialize=capability_data, within=pyo.Reals
    )
    model.cost = pyo.Param(
        model.A, model.R, initialize=cost_data, within=pyo.Reals
    )

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def availability_rule(instance, aircraft_label):
        return (
            sum(instance.x[aircraft_label, route_label] for route_label in instance.R)
            <= instance.availability[aircraft_label]
        )

    model.availability_limits = pyo.Constraint(
        model.A, rule=availability_rule
    )

    def demand_rule(instance, route_label):
        return (
            sum(
                instance.capability[aircraft_label, route_label]
                * instance.x[aircraft_label, route_label]
                for aircraft_label in instance.A
            )
            >= instance.demand[route_label]
        )

    model.demand_requirements = pyo.Constraint(model.R, rule=demand_rule)

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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}