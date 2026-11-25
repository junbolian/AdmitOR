# IR: {"sets":{"N":[0,1,2,3],"A":[[0,1],[0,2],[0,3],[1,0],[1,2],[1,3],[2,0],[2,1],[2,3],[3,0],[3,1],[3,2]]},"params":{"pair_weights":"array indexed by the order of A","facilities_to_select":"required facility count"},"variables":{"x[i]":"binary, i in N","z[i,j]":"binary, (i,j) in A"},"constraints":["sum(x[i] for i in N) = facilities_to_select","z[i,j] <= x[i] for (i,j) in A","z[i,j] <= x[j] for (i,j) in A","z[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(pair_weights[k] * z[i,j] for k,(i,j) in enumerate(A))"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pair_weights = params["pair_weights"]
    facilities_to_select = params["facilities_to_select"]

    ordered_pairs = [
        (0, 1), (0, 2), (0, 3),
        (1, 0), (1, 2), (1, 3),
        (2, 0), (2, 1), (2, 3),
        (3, 0), (3, 1), (3, 2),
    ]

    if len(pair_weights) != len(ordered_pairs):
        raise ValueError("pair_weights must contain exactly 12 coefficients.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 3)
    model.ordered_pairs = pyo.Set(
        dimen=2, initialize=ordered_pairs, ordered=True
    )

    model.weights = pyo.Param(
        model.ordered_pairs,
        initialize={
            pair: pair_weights[position]
            for position, pair in enumerate(ordered_pairs)
        },
        within=pyo.Reals,
    )
    model.required_count = pyo.Param(
        initialize=facilities_to_select, within=pyo.Reals
    )

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.z = pyo.Var(model.ordered_pairs, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.x[i] for i in model.nodes) == model.required_count
    )

    def pair_first_rule(instance, i, j):
        return instance.z[i, j] <= instance.x[i]

    def pair_second_rule(instance, i, j):
        return instance.z[i, j] <= instance.x[j]

    def pair_lower_rule(instance, i, j):
        return instance.z[i, j] >= instance.x[i] + instance.x[j] - 1

    model.pair_first = pyo.Constraint(
        model.ordered_pairs, rule=pair_first_rule
    )
    model.pair_second = pyo.Constraint(
        model.ordered_pairs, rule=pair_second_rule
    )
    model.pair_lower = pyo.Constraint(
        model.ordered_pairs, rule=pair_lower_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.weights[i, j] * model.z[i, j]
            for i, j in model.ordered_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}