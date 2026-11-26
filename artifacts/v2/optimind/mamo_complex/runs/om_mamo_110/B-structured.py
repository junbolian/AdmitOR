# IR: {"sets":{"N":"{0,...,7}","A":"{(i,j) in N x N: i != j}","T":"N \\ {0,7}"},"params":{"line_capacities":{"index":"A","domain":"nonnegative real","source":"params['line_capacities']"}},"variables":{"flow":{"index":"A","type":"nonnegative continuous"}},"constraints":["flow[i,j] <= line_capacities[i,j] for (i,j) in A","sum(flow[j,k] for j != k) == sum(flow[k,j] for j != k) for k in T"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for j != 0) - sum(flow[j,0] for j != 0)"}}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept capacities as a tuple-keyed mapping or nested matrix/mapping."""
    line_capacities = params["line_capacities"]

    model = pyo.ConcreteModel()
    model.stations = pyo.RangeSet(0, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )
    model.transit_stations = pyo.RangeSet(1, 6)

    def capacity_rule(network, i, j):
        if isinstance(line_capacities, Mapping) and (i, j) in line_capacities:
            return line_capacities[i, j]
        return line_capacities[i][j]

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacity_rule,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_limit_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_limit_rule,
    )

    def flow_balance_rule(network, k):
        return (
            sum(network.flow[j, k] for j in network.stations if j != k)
            == sum(network.flow[k, j] for j in network.stations if j != k)
        )

    model.flow_balance = pyo.Constraint(
        model.transit_stations,
        rule=flow_balance_rule,
    )
    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.stations if j != 0)
            - sum(model.flow[j, 0] for j in model.stations if j != 0)
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