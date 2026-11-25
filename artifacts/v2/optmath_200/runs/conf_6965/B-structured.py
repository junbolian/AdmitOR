# IR: {"sets":{"N":[0,1,2,3,4],"A":"{(i,j): i,j in N, i != j}"},"params":{"select_limit":"params['select_limit']","dispersion[i,j]":"params['dispersion']; tuple-key mapping or nested rows"},"variables":{"x[i]":"binary, i in N","y[i,j]":"binary, (i,j) in A"},"constraints":["sum(x[i] for i in N) == select_limit","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(dispersion[i,j] * y[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ],
        ordered=True,
    )

    dispersion_data = params["dispersion"]

    def dispersion_rule(instance, i, j):
        if isinstance(dispersion_data, Mapping) and (i, j) in dispersion_data:
            return dispersion_data[(i, j)]
        return dispersion_data[i][j]

    model.select_limit = pyo.Param(
        initialize=params["select_limit"],
        within=pyo.Reals,
    )
    model.dispersion = pyo.Param(
        model.arcs,
        initialize=dispersion_rule,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.y = pyo.Var(model.arcs, domain=pyo.Binary)

    model.selection_count = pyo.Constraint(
        expr=sum(model.x[i] for i in model.nodes) == model.select_limit
    )

    def activation_first_rule(instance, i, j):
        return instance.y[i, j] <= instance.x[i]

    def activation_second_rule(instance, i, j):
        return instance.y[i, j] <= instance.x[j]

    def activation_lower_rule(instance, i, j):
        return instance.y[i, j] >= instance.x[i] + instance.x[j] - 1

    model.activation_first = pyo.Constraint(
        model.arcs, rule=activation_first_rule
    )
    model.activation_second = pyo.Constraint(
        model.arcs, rule=activation_second_rule
    )
    model.activation_lower = pyo.Constraint(
        model.arcs, rule=activation_lower_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.dispersion[i, j] * model.y[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}