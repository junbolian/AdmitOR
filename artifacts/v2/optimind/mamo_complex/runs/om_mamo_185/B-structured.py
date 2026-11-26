# IR: {"sets":{"cities":"0..7","arcs":"(i,j) in cities x cities with i != j","intermediate":"1..6"},"params":{"capacity":"params['capacity'][i][j], nonnegative, thousands of vehicles/hour"},"variables":{"flow[i,j]":"continuous nonnegative for each arc"},"constraints":["flow[i,j] <= capacity[i][j] for each arc","sum(flow[i,k] for i != k) = sum(flow[k,j] for j != k) for each intermediate city k"],"objective":"maximize sum(flow[0,j] for j != 0) - sum(flow[i,0] for i != 0), in thousands of vehicles/hour"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(0, 7)
    model.intermediate = pyo.RangeSet(1, 6)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )

    model.link_capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): capacity[i][j]
            for i in range(8)
            for j in range(8)
            if i != j
        },
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.link_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, k):
        return (
            sum(network.flow[i, k] for i in network.cities if i != k)
            == sum(network.flow[k, j] for j in network.cities if j != k)
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.cities if j != 0)
            - sum(model.flow[i, 0] for i in model.cities if i != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}