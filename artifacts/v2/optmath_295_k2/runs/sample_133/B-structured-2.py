# IR: {"sets":{"N":[0,1,2,3,4],"P":"{(i,j): i,j in N, i<j}"},"params":{"k":"params['num_facilities_to_select']","d":{"0,1":"params['distance_01']","0,2":"params['distance_02']","0,3":"params['distance_03']","0,4":"params['distance_04']","1,2":"params['distance_12']","1,3":"params['distance_13']","1,4":"params['distance_14']","2,3":"params['distance_23']","2,4":"params['distance_24']","3,4":"params['distance_34']"},"M":"params['large_constant_M']"},"variables":{"x[i]":"Binary, i in N","y[i,j]":"Binary, (i,j) in P","z":"Real"},"constraints":["sum(x[i] for i in N) == k","y[i,j] <= x[i] for (i,j) in P","y[i,j] <= x[j] for (i,j) in P","y[i,j] >= x[i] + x[j] - 1 for (i,j) in P","z + M*y[i,j] <= M + d[i,j] for (i,j) in P"],"objective":"maximize z"}

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
    model.nodes = pyo.RangeSet(0, 4)
    model.pairs = pyo.Set(dimen=2, initialize=distances.keys())

    model.facility_count = pyo.Param(
        initialize=params["num_facilities_to_select"]
    )
    model.big_m = pyo.Param(initialize=params["large_constant_M"])
    model.distance = pyo.Param(model.pairs, initialize=distances)

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_selected = pyo.Var(model.pairs, domain=pyo.Binary)
    model.minimum_distance = pyo.Var(domain=pyo.Reals)

    model.selection_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.nodes)
        == model.facility_count
    )

    def pair_first_rule(current_model, i, j):
        return current_model.pair_selected[i, j] <= current_model.selected[i]

    def pair_second_rule(current_model, i, j):
        return current_model.pair_selected[i, j] <= current_model.selected[j]

    def pair_lower_rule(current_model, i, j):
        return (
            current_model.pair_selected[i, j]
            >= current_model.selected[i] + current_model.selected[j] - 1
        )

    def distance_limit_rule(current_model, i, j):
        return (
            current_model.minimum_distance
            + current_model.big_m * current_model.pair_selected[i, j]
            <= current_model.big_m + current_model.distance[i, j]
        )

    model.pair_first_limit = pyo.Constraint(
        model.pairs, rule=pair_first_rule
    )
    model.pair_second_limit = pyo.Constraint(
        model.pairs, rule=pair_second_rule
    )
    model.pair_lower_limit = pyo.Constraint(
        model.pairs, rule=pair_lower_rule
    )
    model.distance_limit = pyo.Constraint(
        model.pairs, rule=distance_limit_rule
    )

    model.objective = pyo.Objective(
        expr=model.minimum_distance, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}