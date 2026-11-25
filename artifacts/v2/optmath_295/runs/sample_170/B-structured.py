# IR: {"sets":{"A":["aircraft_0","aircraft_1","aircraft_2","aircraft_3","aircraft_4"],"R":["route_0","route_1","route_2","route_3","route_4","route_5"]},"params":{"aircraft_availability":"availability[A]","route_demand":"demand[R]","capacity_coeff":"capacity[A,R], aircraft-major order","operational_cost":"cost[A,R], aircraft-major order"},"variables":{"assigned[A,R]":"nonnegative integer"},"constraints":["For each a in A: sum(assigned[a,r] for r in R) <= availability[a]","For each r in R: sum(capacity[a,r]*assigned[a,r] for a in A) >= demand[r]"],"objective":"minimize sum(cost[a,r]*assigned[a,r] for a in A for r in R)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = tuple(f"aircraft_{i}" for i in range(5))
    routes = tuple(f"route_{j}" for j in range(6))

    availability_data = params["aircraft_availability"]
    demand_data = params["route_demand"]
    capacity_data = params["capacity_coeff"]
    cost_data = params["operational_cost"]

    def vector_value(data, label, position):
        if isinstance(data, Mapping):
            if label in data:
                return data[label]
            return data[position]
        return data[position]

    def matrix_value(data, aircraft_label, route_label, i, j):
        if isinstance(data, Mapping):
            if (aircraft_label, route_label) in data:
                return data[aircraft_label, route_label]
            if (i, j) in data:
                return data[i, j]
            row = (
                data[aircraft_label]
                if aircraft_label in data
                else data[i]
            )
            return vector_value(row, route_label, j)

        if len(data) == len(aircraft) * len(routes):
            return data[i * len(routes) + j]

        return vector_value(data[i], route_label, j)

    availability = {
        aircraft_label: vector_value(
            availability_data, aircraft_label, i
        )
        for i, aircraft_label in enumerate(aircraft)
    }
    demand = {
        route_label: vector_value(demand_data, route_label, j)
        for j, route_label in enumerate(routes)
    }
    capacity = {
        (aircraft_label, route_label): matrix_value(
            capacity_data, aircraft_label, route_label, i, j
        )
        for i, aircraft_label in enumerate(aircraft)
        for j, route_label in enumerate(routes)
    }
    cost = {
        (aircraft_label, route_label): matrix_value(
            cost_data, aircraft_label, route_label, i, j
        )
        for i, aircraft_label in enumerate(aircraft)
        for j, route_label in enumerate(routes)
    }

    model = pyo.ConcreteModel()
    model.A = pyo.Set(initialize=aircraft, ordered=True)
    model.R = pyo.Set(initialize=routes, ordered=True)

    model.availability = pyo.Param(model.A, initialize=availability)
    model.demand = pyo.Param(model.R, initialize=demand)
    model.capacity = pyo.Param(model.A, model.R, initialize=capacity)
    model.cost = pyo.Param(model.A, model.R, initialize=cost)

    model.assigned = pyo.Var(
        model.A, model.R, domain=pyo.NonNegativeIntegers
    )

    def availability_rule(instance, aircraft_label):
        return (
            sum(
                instance.assigned[aircraft_label, route_label]
                for route_label in instance.R
            )
            <= instance.availability[aircraft_label]
        )

    def demand_rule(instance, route_label):
        return (
            sum(
                instance.capacity[aircraft_label, route_label]
                * instance.assigned[aircraft_label, route_label]
                for aircraft_label in instance.A
            )
            >= instance.demand[route_label]
        )

    model.availability_limit = pyo.Constraint(
        model.A, rule=availability_rule
    )
    model.route_coverage = pyo.Constraint(model.R, rule=demand_rule)

    model.total_operational_cost = pyo.Objective(
        expr=sum(
            model.cost[aircraft_label, route_label]
            * model.assigned[aircraft_label, route_label]
            for aircraft_label in model.A
            for route_label in model.R
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when no feasible solution can be loaded.
        # Leave success determination to objective evaluation below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_operational_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}