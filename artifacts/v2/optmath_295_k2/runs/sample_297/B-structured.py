# IR: {"sets":{"N":[0,1,2,3],"A":"{(i,j) in N x N: i != j}"},"params":{"num_facilities":"params['num_facilities']","big_M":"params['big_M']","distance[i,j]":"params['distance_'+str(i)+'_'+str(j)] for (i,j) in A"},"variables":{"selected[i]":"Binary, i in N","pair_selected[i,j]":"Binary, (i,j) in A","min_distance":"Real"},"constraints":["sum(selected[i] for i in N) = num_facilities","min_distance <= distance[i,j] + big_M*(1-pair_selected[i,j]) for (i,j) in A","pair_selected[i,j] <= selected[i] for (i,j) in A","pair_selected[i,j] <= selected[j] for (i,j) in A","pair_selected[i,j] >= selected[i]+selected[j]-1 for (i,j) in A"],"objective":"maximize min_distance"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=range(4), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(4) for j in range(4) if i != j],
        ordered=True,
    )

    model.num_facilities = pyo.Param(initialize=params["num_facilities"])
    model.big_M = pyo.Param(initialize=params["big_M"])
    model.distance = pyo.Param(
        model.A,
        initialize={
            (i, j): params[f"distance_{i}_{j}"]
            for i, j in model.A
        },
    )

    model.selected = pyo.Var(model.N, domain=pyo.Binary)
    model.pair_selected = pyo.Var(model.A, domain=pyo.Binary)
    model.min_distance = pyo.Var(domain=pyo.Reals)

    model.facility_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.N) == model.num_facilities
    )

    def distance_rule(mdl, i, j):
        return mdl.min_distance <= (
            mdl.distance[i, j] + mdl.big_M * (1 - mdl.pair_selected[i, j])
        )

    model.distance_limits = pyo.Constraint(model.A, rule=distance_rule)

    def pair_first_rule(mdl, i, j):
        return mdl.pair_selected[i, j] <= mdl.selected[i]

    model.pair_first_limits = pyo.Constraint(model.A, rule=pair_first_rule)

    def pair_second_rule(mdl, i, j):
        return mdl.pair_selected[i, j] <= mdl.selected[j]

    model.pair_second_limits = pyo.Constraint(model.A, rule=pair_second_rule)

    def pair_lower_rule(mdl, i, j):
        return (
            mdl.pair_selected[i, j] >= mdl.selected[i] + mdl.selected[j] - 1
        )

    model.pair_lower_limits = pyo.Constraint(model.A, rule=pair_lower_rule)
    model.dispersion_objective = pyo.Objective(
        expr=model.min_distance, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.dispersion_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}