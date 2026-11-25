# IR: {
#   "sets": {"T": [0,1,2,3,4,5,6,7], "E": [[0,1],[2,4],[2,7],[3,7],[1,4],[2,3],[0,5],[2,5],[3,5]]},
#   "params": {"bandwidth[i]": "params['bandwidth'][i], i in T", "U": "sum(bandwidth[i] for i in T)"},
#   "variables": {"start[i]": "continuous, 0 <= start[i] <= U-bandwidth[i]", "span": "continuous, 0 <= span <= U", "order[i,j]": "binary, (i,j) in E"},
#   "constraints": [
#     "start[i] + bandwidth[i] <= span, for every i in T",
#     "start[i] + bandwidth[i] <= start[j] + U*(1-order[i,j]), for every (i,j) in E",
#     "start[j] + bandwidth[j] <= start[i] + U*order[i,j], for every (i,j) in E"
#   ],
#   "objective": "minimize span; allocations are half-open intervals [start[i], start[i]+bandwidth[i])"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    towers = tuple(range(8))
    edges = (
        (0, 1),
        (2, 4),
        (2, 7),
        (3, 7),
        (1, 4),
        (2, 3),
        (0, 5),
        (2, 5),
        (3, 5),
    )
    bandwidth = {i: params["bandwidth"][i] for i in towers}
    upper_bound = sum(bandwidth[i] for i in towers)

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=towers, ordered=True)
    model.E = pyo.Set(initialize=edges, dimen=2, ordered=True)

    model.bandwidth = pyo.Param(
        model.T, initialize=bandwidth, within=pyo.NonNegativeReals
    )
    model.U = pyo.Param(
        initialize=upper_bound, within=pyo.NonNegativeReals
    )

    def start_bounds(instance, i):
        return (0, upper_bound - bandwidth[i])

    model.start = pyo.Var(
        model.T, domain=pyo.NonNegativeReals, bounds=start_bounds
    )
    model.span = pyo.Var(
        domain=pyo.NonNegativeReals, bounds=(0, upper_bound)
    )
    model.order = pyo.Var(model.E, domain=pyo.Binary)

    def span_rule(instance, i):
        return instance.start[i] + instance.bandwidth[i] <= instance.span

    model.span_limits = pyo.Constraint(model.T, rule=span_rule)

    def forward_rule(instance, i, j):
        return (
            instance.start[i] + instance.bandwidth[i]
            <= instance.start[j] + instance.U * (1 - instance.order[i, j])
        )

    model.forward_separation = pyo.Constraint(model.E, rule=forward_rule)

    def reverse_rule(instance, i, j):
        return (
            instance.start[j] + instance.bandwidth[j]
            <= instance.start[i] + instance.U * instance.order[i, j]
        )

    model.reverse_separation = pyo.Constraint(model.E, rule=reverse_rule)

    model.spectrum_objective = pyo.Objective(
        expr=model.span, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Let unrelated runtime errors propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.spectrum_objective))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}