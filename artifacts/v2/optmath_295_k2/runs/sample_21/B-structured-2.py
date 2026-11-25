# IR: {"sets":{"N":[0,1,2,3,4],"A":"[(i,j) for i in N for j in N if i != j]"},"params":{"d[A]":"params['pairwise_distances'] in A order","k":"params['num_facilities_to_open']"},"variables":{"x[N]":"binary","y[A]":"binary"},"constraints":["sum(x[i] for i in N) == k","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(d[i,j] * y[i,j] for (i,j) in A)"}

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
    facilities_to_open = params["num_facilities_to_open"]

    if len(distances) != len(ordered_pairs):
        raise ValueError(
            "pairwise_distances must contain one value per ordered distinct pair."
        )

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=ordered_pairs, ordered=True)

    model.d = pyo.Param(
        model.A,
        initialize={
            pair: distances[position]
            for position, pair in enumerate(ordered_pairs)
        },
        within=pyo.Reals,
    )
    model.k = pyo.Param(
        initialize=facilities_to_open,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.y = pyo.Var(model.A, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.x[i] for i in model.N) == model.k
    )

    def first_endpoint_rule(instance, i, j):
        return instance.y[i, j] <= instance.x[i]

    def second_endpoint_rule(instance, i, j):
        return instance.y[i, j] <= instance.x[j]

    def both_endpoints_rule(instance, i, j):
        return instance.y[i, j] >= instance.x[i] + instance.x[j] - 1

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
            model.d[i, j] * model.y[i, j]
            for i, j in model.A
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}