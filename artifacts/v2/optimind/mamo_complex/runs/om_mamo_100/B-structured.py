# IR: {"sets":{"N":"0..8","T":"1..7","A":"N x N"},"params":{"capacity_matrix":"params['capacity_matrix']; directed capacities indexed [origin][destination]"},"variables":{"flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["flow[i,j] <= capacity_matrix[i][j] for (i,j) in A","sum(flow[i,k] for i in N) = sum(flow[k,j] for j in N) for k in T"],"objective":"maximize sum(flow[0,j] for j in N) - sum(flow[i,0] for i in N)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_matrix = params["capacity_matrix"]

    model = pyo.ConcreteModel()
    model.hubs = pyo.RangeSet(0, 8)
    model.transit_hubs = pyo.RangeSet(1, 7)

    model.route_capacity = pyo.Param(
        model.hubs,
        model.hubs,
        initialize=lambda mdl, origin, destination: capacity_matrix[origin][
            destination
        ],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.hubs,
        model.hubs,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(mdl, origin, destination):
        return (
            mdl.flow[origin, destination]
            <= mdl.route_capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.hubs,
        model.hubs,
        rule=capacity_rule,
    )

    def conservation_rule(mdl, hub):
        return (
            sum(mdl.flow[origin, hub] for origin in mdl.hubs)
            == sum(mdl.flow[hub, destination] for destination in mdl.hubs)
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_hubs,
        rule=conservation_rule,
    )

    model.net_source_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, destination] for destination in model.hubs)
            - sum(model.flow[origin, 0] for origin in model.hubs)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.net_source_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}