# IR: {"sets":{"N":[0,1,2,3,4],"A":"[(i,j) for i in N for j in N if i != j]"},"params":{"pairwise_distances":"real vector indexed in A order","num_facilities_to_open":"real scalar"},"variables":{"x[i]":"binary, i in N","y[i,j]":"binary, (i,j) in A"},"constraints":["sum(x[i] for i in N) == num_facilities_to_open","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(pairwise_distances[i,j] * y[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(5))
    ordered_pairs = [
        (i, j)
        for i in nodes
        for j in nodes
        if i != j
    ]

    distances = params["pairwise_distances"]
    facility_count = params["num_facilities_to_open"]

    if len(distances) != len(ordered_pairs):
        raise ValueError(
            "pairwise_distances must contain one value per ordered pair."
        )

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=ordered_pairs, ordered=True)

    model.distance = pyo.Param(
        model.A,
        initialize={
            pair: distances[position]
            for position, pair in enumerate(ordered_pairs)
        },
        within=pyo.Reals,
    )
    model.facility_count = pyo.Param(
        initialize=facility_count,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.y = pyo.Var(model.A, domain=pyo.Binary)

    model.total_facilities = pyo.Constraint(
        expr=sum(model.x[i] for i in model.N) == model.facility_count
    )

    def first_endpoint_rule(current_model, i, j):
        return current_model.y[i, j] <= current_model.x[i]

    def second_endpoint_rule(current_model, i, j):
        return current_model.y[i, j] <= current_model.x[j]

    def both_endpoints_rule(current_model, i, j):
        return (
            current_model.y[i, j]
            >= current_model.x[i] + current_model.x[j] - 1
        )

    model.first_endpoint = pyo.Constraint(
        model.A, rule=first_endpoint_rule
    )
    model.second_endpoint = pyo.Constraint(
        model.A, rule=second_endpoint_rule
    )
    model.both_endpoints = pyo.Constraint(
        model.A, rule=both_endpoints_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.y[i, j]
            for i, j in model.A
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