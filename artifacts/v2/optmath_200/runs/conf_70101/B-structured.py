# IR: {"sets":{"N":[0,1,2,3,4],"A":"{(i,j) in N x N: i != j}"},"params":{"pair_score_i_j":"params['pair_score_i_j'] for every (i,j) in A"},"variables":{"x[i]":"binary, i in N","y[i,j]":"binary, (i,j) in A"},"constraints":["sum(x[i] for i in N) == 2","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(pair_score_i_j * y[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    scores = {
        (0, 1): params["pair_score_0_1"],
        (0, 2): params["pair_score_0_2"],
        (0, 3): params["pair_score_0_3"],
        (0, 4): params["pair_score_0_4"],
        (1, 0): params["pair_score_1_0"],
        (1, 2): params["pair_score_1_2"],
        (1, 3): params["pair_score_1_3"],
        (1, 4): params["pair_score_1_4"],
        (2, 0): params["pair_score_2_0"],
        (2, 1): params["pair_score_2_1"],
        (2, 3): params["pair_score_2_3"],
        (2, 4): params["pair_score_2_4"],
        (3, 0): params["pair_score_3_0"],
        (3, 1): params["pair_score_3_1"],
        (3, 2): params["pair_score_3_2"],
        (3, 4): params["pair_score_3_4"],
        (4, 0): params["pair_score_4_0"],
        (4, 1): params["pair_score_4_1"],
        (4, 2): params["pair_score_4_2"],
        (4, 3): params["pair_score_4_3"],
    }

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=range(5), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(5)
            for j in range(5)
            if i != j
        ],
        ordered=True,
    )
    model.pair_score = pyo.Param(
        model.A, initialize=scores, within=pyo.Reals
    )

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.y = pyo.Var(model.A, domain=pyo.Binary)

    model.select_two = pyo.Constraint(
        expr=sum(model.x[i] for i in model.N) == 2
    )

    def pair_first_rule(instance, i, j):
        return instance.y[i, j] <= instance.x[i]

    def pair_second_rule(instance, i, j):
        return instance.y[i, j] <= instance.x[j]

    def pair_lower_rule(instance, i, j):
        return (
            instance.y[i, j]
            >= instance.x[i] + instance.x[j] - 1
        )

    model.pair_first = pyo.Constraint(
        model.A, rule=pair_first_rule
    )
    model.pair_second = pyo.Constraint(
        model.A, rule=pair_second_rule
    )
    model.pair_lower = pyo.Constraint(
        model.A, rule=pair_lower_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.pair_score[i, j] * model.y[i, j]
            for i, j in model.A
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