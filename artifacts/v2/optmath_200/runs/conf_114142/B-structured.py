# IR: {"sets":{"N":[0,1,2,3,4],"A":"[(i,j) for i in N for j in N if i != j]"},"params":{"dispersion_weights":"weights indexed by A in listed order","total_facilities":"required number of selected facilities"},"variables":{"x[i]":"binary, i in N","y[i,j]":"binary, (i,j) in A"},"constraints":["sum(x[i] for i in N) == total_facilities","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(dispersion_weights[i,j] * y[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(5))
    pairs = [(i, j) for i in nodes for j in nodes if i != j]
    weights = params["dispersion_weights"]
    required_facilities = params["total_facilities"]

    if len(weights) != len(pairs):
        raise ValueError("dispersion_weights must contain exactly 20 entries.")

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.A = pyo.Set(initialize=pairs, dimen=2, ordered=True)

    model.dispersion_weights = pyo.Param(
        model.A,
        initialize={pair: weights[k] for k, pair in enumerate(pairs)},
        within=pyo.Reals,
    )
    model.total_facilities = pyo.Param(
        initialize=required_facilities, within=pyo.Reals
    )

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.y = pyo.Var(model.A, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.x[i] for i in model.N) == model.total_facilities
    )
    model.pair_first = pyo.Constraint(
        model.A, rule=lambda mdl, i, j: mdl.y[i, j] <= mdl.x[i]
    )
    model.pair_second = pyo.Constraint(
        model.A, rule=lambda mdl, i, j: mdl.y[i, j] <= mdl.x[j]
    )
    model.pair_lower = pyo.Constraint(
        model.A,
        rule=lambda mdl, i, j: mdl.y[i, j] >= mdl.x[i] + mdl.x[j] - 1,
    )

    model.dispersion_objective = pyo.Objective(
        expr=sum(
            model.dispersion_weights[i, j] * model.y[i, j]
            for i, j in model.A
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.dispersion_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}