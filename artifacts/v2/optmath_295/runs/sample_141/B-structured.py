# IR: {"sets":{"N":[0,1,2,3],"A":"{(i,j) in N x N: i != j}"},"params":{"weights":"real weights[i,j] = params['weights_'+str(i)+str(j)] for (i,j) in A","facilities_to_select":"real = params['facilities_to_select']"},"variables":{"x[i]":"binary for i in N","z[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[i] for i in N) = facilities_to_select","z[i,j] <= x[i] for (i,j) in A","z[i,j] <= x[j] for (i,j) in A","z[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(weights[i,j] * z[i,j] for (i,j) in A)"}

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

    model.weights = pyo.Param(
        model.pairs,
        within=pyo.Reals,
        initialize={
            (0, 1): params["weights_01"],
            (0, 2): params["weights_02"],
            (0, 3): params["weights_03"],
            (1, 0): params["weights_10"],
            (1, 2): params["weights_12"],
            (1, 3): params["weights_13"],
            (2, 0): params["weights_20"],
            (2, 1): params["weights_21"],
            (2, 3): params["weights_23"],
            (3, 0): params["weights_30"],
            (3, 1): params["weights_31"],
            (3, 2): params["weights_32"],
        },
    )
    model.facilities_to_select = pyo.Param(
        within=pyo.Reals,
        initialize=params["facilities_to_select"],
    )

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.z = pyo.Var(model.pairs, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.x[i] for i in model.nodes)
        == model.facilities_to_select
    )

    def pair_first_rule(mdl, i, j):
        return mdl.z[i, j] <= mdl.x[i]

    def pair_second_rule(mdl, i, j):
        return mdl.z[i, j] <= mdl.x[j]

    def pair_lower_rule(mdl, i, j):
        return mdl.z[i, j] >= mdl.x[i] + mdl.x[j] - 1

    model.pair_first = pyo.Constraint(model.pairs, rule=pair_first_rule)
    model.pair_second = pyo.Constraint(model.pairs, rule=pair_second_rule)
    model.pair_lower = pyo.Constraint(model.pairs, rule=pair_lower_rule)

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.weights[i, j] * model.z[i, j]
            for i, j in model.pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}