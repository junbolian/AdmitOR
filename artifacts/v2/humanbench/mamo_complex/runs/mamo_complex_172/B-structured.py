# IR: {"sets":{"V":"0..8","A":"{(i,j) in V x V: i != j}","T":"1..7"},"params":{"capacity":"params['capacity'], a nonnegative 9x9 matrix"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[v,j] for j != v) = sum(flow[i,v] for i != v) for v in T"],"objective":"maximize sum(flow[0,j] for j != 0) - sum(flow[i,0] for i != 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_data = params["capacity"]

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(0, 8)
    model.transit_cities = pyo.RangeSet(1, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(9)
            for destination in range(9)
            if origin != destination
        ],
    )

    model.arc_capacity = pyo.Param(
        model.cities,
        model.cities,
        initialize=lambda mdl, origin, destination: capacity_data[origin][destination],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, origin, destination):
        return mdl.flow[origin, destination] <= mdl.arc_capacity[origin, destination]

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(mdl, city):
        return (
            sum(
                mdl.flow[city, destination]
                for destination in mdl.cities
                if destination != city
            )
            == sum(
                mdl.flow[origin, city]
                for origin in mdl.cities
                if origin != city
            )
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_cities, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, destination] for destination in model.cities if destination != 0)
            - sum(model.flow[origin, 0] for origin in model.cities if origin != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}