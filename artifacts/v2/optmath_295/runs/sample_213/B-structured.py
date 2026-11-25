# IR: {"sets":{"N":"range(num_locations)","A":"{(i,j) in N x N: i != j}"},"params":{"num_locations":"params['num_locations']","num_facilities_to_select":"params['num_facilities_to_select']","dispersion_weights":"params['dispersion_weights']; w[i,j] = dispersion_weights[i*num_locations+j]"},"variables":{"x[i]":"binary, i in N","y[i,j]":"binary, (i,j) in A"},"constraints":["sum(x[i] for i in N) = num_facilities_to_select","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(w[i,j]*y[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_locations = params["num_locations"]
    num_facilities_to_select = params["num_facilities_to_select"]
    dispersion_weights = params["dispersion_weights"]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(
        initialize=range(num_locations),
        ordered=True,
    )
    model.A = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_locations)
            for j in range(num_locations)
            if i != j
        ),
        ordered=True,
    )

    model.required_facilities = pyo.Param(
        initialize=num_facilities_to_select,
        within=pyo.NonNegativeIntegers,
    )
    model.weights = pyo.Param(
        model.A,
        initialize={
            (i, j): dispersion_weights[i * num_locations + j]
            for i, j in model.A
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.y = pyo.Var(model.A, domain=pyo.Binary)

    # Explicit expressions preserve a valid constraint even for an empty set.
    model.selected_count = pyo.Expression(
        expr=sum(model.x[i] for i in model.N)
    )
    model.facility_count = pyo.Constraint(
        expr=model.selected_count == model.required_facilities
    )

    def first_endpoint_rule(instance, i, j):
        return instance.y[i, j] <= instance.x[i]

    def second_endpoint_rule(instance, i, j):
        return instance.y[i, j] <= instance.x[j]

    def activation_rule(instance, i, j):
        return instance.y[i, j] >= instance.x[i] + instance.x[j] - 1

    model.first_endpoint = pyo.Constraint(
        model.A, rule=first_endpoint_rule
    )
    model.second_endpoint = pyo.Constraint(
        model.A, rule=second_endpoint_rule
    )
    model.pair_activation = pyo.Constraint(
        model.A, rule=activation_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.weights[i, j] * model.y[i, j]
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}