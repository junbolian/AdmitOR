# IR: {"sets":{"N":"{0,1,2,3,4}","A":"{(i,j) in N x N: i != j}"},"params":{"weights":"real w[i,j] = params['weights'][i][j] for (i,j) in A","num_facilities":"real k = params['num_facilities']"},"variables":{"x[i]":"binary for i in N","y[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[i] for i in N) = k","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(w[i,j] * y[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(5), ordered=True)
    model.ordered_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ],
        ordered=True,
    )

    model.weights = pyo.Param(
        model.ordered_pairs,
        initialize={
            (i, j): params["weights"][i][j]
            for i, j in model.ordered_pairs
        },
        within=pyo.Reals,
    )
    model.num_facilities = pyo.Param(
        initialize=params["num_facilities"],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.y = pyo.Var(model.ordered_pairs, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.x[i] for i in model.nodes) == model.num_facilities
    )

    def activation_first_rule(model, i, j):
        return model.y[i, j] <= model.x[i]

    def activation_second_rule(model, i, j):
        return model.y[i, j] <= model.x[j]

    def activation_lower_rule(model, i, j):
        return model.y[i, j] >= model.x[i] + model.x[j] - 1

    model.activation_first = pyo.Constraint(
        model.ordered_pairs, rule=activation_first_rule
    )
    model.activation_second = pyo.Constraint(
        model.ordered_pairs, rule=activation_second_rule
    )
    model.activation_lower = pyo.Constraint(
        model.ordered_pairs, rule=activation_lower_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.weights[i, j] * model.y[i, j]
            for i, j in model.ordered_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Continue to the objective-value check; propagate unrelated errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}