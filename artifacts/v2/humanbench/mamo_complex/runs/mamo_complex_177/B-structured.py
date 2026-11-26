# IR: {"sets":{"H":"{0,...,6}","A":"{(i,j) in H x H: i != j}"},"params":{"capacities":"Nonnegative 7x7 matrix from params['capacities']"},"variables":{"flow[i,j]":"Nonnegative real for (i,j) in A","throughput":"Nonnegative real"},"constraints":["flow[i,j] <= capacities[i][j] for every (i,j) in A","sum_j flow[i,j] - sum_j flow[j,i] = throughput if i=0, -throughput if i=6, and 0 otherwise"],"objective":"Maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve maximum flow from hub 0 to hub 6 using a 7x7 capacity matrix."""
    capacities = params["capacities"]

    model = pyo.ConcreteModel()
    model.hubs = pyo.RangeSet(0, 6)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(7)
            for destination in range(7)
            if origin != destination
        ],
    )

    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize=lambda mdl, origin, destination: capacities[origin][destination],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, origin, destination):
        return mdl.flow[origin, destination] <= mdl.arc_capacity[origin, destination]

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(mdl, hub):
        outgoing = sum(
            mdl.flow[hub, destination]
            for destination in mdl.hubs
            if destination != hub
        )
        incoming = sum(
            mdl.flow[origin, hub]
            for origin in mdl.hubs
            if origin != hub
        )

        if hub == 0:
            return outgoing - incoming == mdl.throughput
        if hub == 6:
            return outgoing - incoming == -mdl.throughput
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(model.hubs, rule=balance_rule)
    model.max_throughput = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.max_throughput))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}