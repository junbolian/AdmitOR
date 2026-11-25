# {
#   "sets": {"N": [0, 1, 2, 3, 4], "A": "ordered pairs (i,j) in N x N with i != j, row-major"},
#   "params": {"d[i,j]": "params['coverage_scores'] mapped onto A", "k": "params['num_centers']"},
#   "variables": {"x[i]": "binary, i in N", "z[i,j]": "binary, (i,j) in A"},
#   "constraints": [
#     "sum(x[i] for i in N) == k",
#     "z[i,j] <= x[i] for each (i,j) in A",
#     "z[i,j] <= x[j] for each (i,j) in A",
#     "z[i,j] >= x[i] + x[j] - 1 for each (i,j) in A"
#   ],
#   "objective": "maximize sum(d[i,j] * z[i,j] for (i,j) in A)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = range(5)
    pairs = [(i, j) for i in nodes for j in nodes if i != j]
    coverage_scores = list(params["coverage_scores"])
    num_centers = params["num_centers"]

    if len(coverage_scores) != len(pairs):
        return {"objective": None, "status": "invalid_coverage_scores"}

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=pairs, ordered=True)

    model.d = pyo.Param(
        model.A,
        initialize=dict(zip(pairs, coverage_scores)),
        within=pyo.Reals,
    )
    model.k = pyo.Param(initialize=num_centers, within=pyo.Reals)

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.z = pyo.Var(model.A, domain=pyo.Binary)

    model.center_count = pyo.Constraint(
        expr=sum(model.x[i] for i in model.N) == model.k
    )

    def pair_upper_first_rule(model, i, j):
        return model.z[i, j] <= model.x[i]

    def pair_upper_second_rule(model, i, j):
        return model.z[i, j] <= model.x[j]

    def pair_lower_rule(model, i, j):
        return model.z[i, j] >= model.x[i] + model.x[j] - 1

    model.pair_upper_first = pyo.Constraint(
        model.A, rule=pair_upper_first_rule
    )
    model.pair_upper_second = pyo.Constraint(
        model.A, rule=pair_upper_second_rule
    )
    model.pair_lower = pyo.Constraint(model.A, rule=pair_lower_rule)

    model.total_coverage = pyo.Objective(
        expr=sum(model.d[i, j] * model.z[i, j] for i, j in model.A),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_coverage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}