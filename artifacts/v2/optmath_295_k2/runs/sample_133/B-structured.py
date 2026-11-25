# IR: {"sets":{"N":[0,1,2,3,4],"P":"{(i,j): i,j in N and i<j}"},"params":["num_facilities_to_select","distance_01","distance_02","distance_03","distance_04","distance_12","distance_13","distance_14","distance_23","distance_24","distance_34","large_constant_M"],"decision_variables":{"x[i]":"binary, i in N","y[i,j]":"binary, (i,j) in P","D":"nonnegative continuous"},"constraints":["sum(x[i] for i in N) = num_facilities_to_select","y[i,j] <= x[i] for (i,j) in P","y[i,j] <= x[j] for (i,j) in P","y[i,j] >= x[i] + x[j] - 1 for (i,j) in P","D + large_constant_M*y[i,j] <= large_constant_M + distance_ij for (i,j) in P"],"objective":"maximize D"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distances = {
        (0, 1): params["distance_01"],
        (0, 2): params["distance_02"],
        (0, 3): params["distance_03"],
        (0, 4): params["distance_04"],
        (1, 2): params["distance_12"],
        (1, 3): params["distance_13"],
        (1, 4): params["distance_14"],
        (2, 3): params["distance_23"],
        (2, 4): params["distance_24"],
        (3, 4): params["distance_34"],
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(5), ordered=True)
    model.pairs = pyo.Set(
        dimen=2, initialize=distances.keys(), ordered=True
    )

    model.facility_count = pyo.Param(
        initialize=params["num_facilities_to_select"]
    )
    model.big_m = pyo.Param(initialize=params["large_constant_M"])
    model.pair_distance = pyo.Param(model.pairs, initialize=distances)

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_selected = pyo.Var(model.pairs, domain=pyo.Binary)
    model.minimum_distance = pyo.Var(domain=pyo.NonNegativeReals)

    model.selection_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.nodes)
        == model.facility_count
    )

    def pair_first_upper_rule(model, i, j):
        return model.pair_selected[i, j] <= model.selected[i]

    def pair_second_upper_rule(model, i, j):
        return model.pair_selected[i, j] <= model.selected[j]

    def pair_lower_rule(model, i, j):
        return (
            model.pair_selected[i, j]
            >= model.selected[i] + model.selected[j] - 1
        )

    def distance_limit_rule(model, i, j):
        return (
            model.minimum_distance
            + model.big_m * model.pair_selected[i, j]
            <= model.big_m + model.pair_distance[i, j]
        )

    model.pair_first_upper = pyo.Constraint(
        model.pairs, rule=pair_first_upper_rule
    )
    model.pair_second_upper = pyo.Constraint(
        model.pairs, rule=pair_second_upper_rule
    )
    model.pair_lower = pyo.Constraint(model.pairs, rule=pair_lower_rule)
    model.distance_limit = pyo.Constraint(
        model.pairs, rule=distance_limit_rule
    )

    model.dispersion_objective = pyo.Objective(
        expr=model.minimum_distance, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.dispersion_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}