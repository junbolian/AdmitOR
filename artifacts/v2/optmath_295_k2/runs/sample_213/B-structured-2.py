# IR: {"sets":{"N":[0,1,2,3,4],"A":"{(i,j) in N x N: i != j}"},"params":{"selection_count":"params['selection_count']","weight[i,j]":"params[f'weight_{i}_{j}'] for (i,j) in A"},"variables":{"x[i]":"binary, i in N","y[i,j]":"binary, (i,j) in A"},"constraints":["sum(x[i] for i in N) == selection_count","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(weight[i,j] * y[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(5)
            for j in range(5)
            if i != j
        ],
        ordered=True,
    )

    model.selection_count = pyo.Param(
        initialize=params["selection_count"],
        within=pyo.Reals,
    )
    model.dispersion_weight = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"weight_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.y = pyo.Var(model.arcs, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.x[i] for i in model.nodes)
        == model.selection_count
    )

    def first_endpoint_rule(current_model, i, j):
        return current_model.y[i, j] <= current_model.x[i]

    model.first_endpoint = pyo.Constraint(
        model.arcs, rule=first_endpoint_rule
    )

    def second_endpoint_rule(current_model, i, j):
        return current_model.y[i, j] <= current_model.x[j]

    model.second_endpoint = pyo.Constraint(
        model.arcs, rule=second_endpoint_rule
    )

    def activation_rule(current_model, i, j):
        return (
            current_model.y[i, j]
            >= current_model.x[i] + current_model.x[j] - 1
        )

    model.required_activation = pyo.Constraint(
        model.arcs, rule=activation_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.dispersion_weight[i, j] * model.y[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Continue to objective retrieval; propagate unrelated errors.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}