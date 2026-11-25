# IR: {"sets":{"N":[0,1,2,3],"A":"{(i,j) in N x N: i != j}"},"params":{"num_facilities":"required facility count","big_M":"distance relaxation constant","distance_i_j":"params['distance_i_j'] for every (i,j) in A"},"variables":{"selected[i]":"binary for i in N","pair_selected[i,j]":"binary for (i,j) in A","min_distance":"real"},"constraints":["sum(selected[i] for i in N) == num_facilities","min_distance <= distance_i_j + big_M*(1-pair_selected[i,j]) for (i,j) in A","pair_selected[i,j] <= selected[i] for (i,j) in A","pair_selected[i,j] <= selected[j] for (i,j) in A","pair_selected[i,j] >= selected[i]+selected[j]-1 for (i,j) in A"],"objective":"maximize min_distance"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(4), ordered=True)
    model.pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(4)
            for j in range(4)
            if i != j
        ],
        ordered=True,
    )

    model.required_count = pyo.Param(
        initialize=params["num_facilities"]
    )
    model.distance_relaxation = pyo.Param(
        initialize=params["big_M"]
    )
    model.distances = pyo.Param(
        model.pairs,
        initialize={
            (i, j): params[f"distance_{i}_{j}"]
            for i, j in model.pairs
        },
    )

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_selected = pyo.Var(model.pairs, domain=pyo.Binary)
    model.min_distance = pyo.Var(domain=pyo.Reals)

    model.facility_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.nodes)
        == model.required_count
    )

    def distance_rule(mod, i, j):
        return (
            mod.min_distance
            <= mod.distances[i, j]
            + mod.distance_relaxation * (1 - mod.pair_selected[i, j])
        )

    def pair_first_rule(mod, i, j):
        return mod.pair_selected[i, j] <= mod.selected[i]

    def pair_second_rule(mod, i, j):
        return mod.pair_selected[i, j] <= mod.selected[j]

    def pair_lower_rule(mod, i, j):
        return (
            mod.pair_selected[i, j]
            >= mod.selected[i] + mod.selected[j] - 1
        )

    model.distance_limits = pyo.Constraint(
        model.pairs, rule=distance_rule
    )
    model.pair_first_limits = pyo.Constraint(
        model.pairs, rule=pair_first_rule
    )
    model.pair_second_limits = pyo.Constraint(
        model.pairs, rule=pair_second_rule
    )
    model.pair_lower_limits = pyo.Constraint(
        model.pairs, rule=pair_lower_rule
    )

    model.dispersion_objective = pyo.Objective(
        expr=model.min_distance,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.dispersion_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}