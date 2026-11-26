# IR: {
#   "sets": {"N": "0..7", "A": "(i,j) in N x N where i != j"},
#   "params": {"capacity[i,j]": "params[f'capacity_{i}_{j}'] for every (i,j) in A"},
#   "variables": {"flow[i,j]": "continuous nonnegative for (i,j) in A", "total_flow": "continuous nonnegative"},
#   "constraints": [
#     "flow[i,j] <= capacity[i,j] for every (i,j) in A",
#     "sum_j flow[0,j] - sum_j flow[j,0] = total_flow",
#     "sum_j flow[i,j] - sum_j flow[j,i] = 0 for i in 1..6",
#     "sum_j flow[7,j] - sum_j flow[j,7] = -total_flow"
#   ],
#   "objective": "maximize total_flow"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.hubs = pyo.RangeSet(0, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(8)
            for destination in range(8)
            if origin != destination
        ],
    )

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"capacity_{origin}_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(network, hub):
        outgoing = sum(
            network.flow[hub, neighbor]
            for neighbor in network.hubs
            if neighbor != hub
        )
        incoming = sum(
            network.flow[neighbor, hub]
            for neighbor in network.hubs
            if neighbor != hub
        )

        if hub == 0:
            return outgoing - incoming == network.total_flow
        if hub == 7:
            return outgoing - incoming == -network.total_flow
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(
        model.hubs, rule=balance_rule
    )

    model.max_flow_objective = pyo.Objective(
        expr=model.total_flow,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}