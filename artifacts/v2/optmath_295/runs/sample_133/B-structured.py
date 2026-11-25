# IR: {"sets":{"N":"range(n_nodes)","E":"{(i,j): i,j in N, i<j}"},"params":{"p":"params['p']","n_nodes":"params['n_nodes']","big_M":"params['big_M']","distance[i,j]":"params['dist_i_j'] for (i,j) in E"},"variables":{"selected[i]":"Binary, i in N","pair_selected[i,j]":"Binary, (i,j) in E","min_distance":"NonNegativeReals"},"constraints":["sum(selected[i] for i in N) == p","pair_selected[i,j] <= selected[i] for (i,j) in E","pair_selected[i,j] <= selected[j] for (i,j) in E","pair_selected[i,j] >= selected[i] + selected[j] - 1 for (i,j) in E","min_distance + big_M*pair_selected[i,j] <= big_M + distance[i,j] for (i,j) in E"],"objective":"maximize min_distance"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.facility_count = pyo.Param(
        initialize=params["p"], within=pyo.NonNegativeIntegers
    )
    model.node_count = pyo.Param(
        initialize=params["n_nodes"], within=pyo.NonNegativeIntegers
    )
    model.big_constant = pyo.Param(
        initialize=params["big_M"], within=pyo.NonNegativeReals
    )

    model.nodes = pyo.Set(
        initialize=range(int(pyo.value(model.node_count))),
        ordered=True,
    )
    model.pairs = pyo.Set(
        dimen=2,
        initialize=[
            (left, right)
            for left in model.nodes
            for right in model.nodes
            if left < right
        ],
        ordered=True,
    )

    distance_data = {
        (0, 1): params["dist_0_1"],
        (0, 2): params["dist_0_2"],
        (0, 3): params["dist_0_3"],
        (0, 4): params["dist_0_4"],
        (1, 2): params["dist_1_2"],
        (1, 3): params["dist_1_3"],
        (1, 4): params["dist_1_4"],
        (2, 3): params["dist_2_3"],
        (2, 4): params["dist_2_4"],
        (3, 4): params["dist_3_4"],
    }
    model.distance = pyo.Param(
        model.pairs,
        initialize=lambda instance, left, right: distance_data[left, right],
        within=pyo.NonNegativeReals,
    )

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_selected = pyo.Var(model.pairs, domain=pyo.Binary)
    model.min_distance = pyo.Var(domain=pyo.NonNegativeReals)

    model.selection_count = pyo.Constraint(
        expr=pyo.quicksum(model.selected[node] for node in model.nodes)
        == model.facility_count
    )

    def pair_left_rule(instance, left, right):
        return instance.pair_selected[left, right] <= instance.selected[left]

    def pair_right_rule(instance, left, right):
        return instance.pair_selected[left, right] <= instance.selected[right]

    def pair_lower_rule(instance, left, right):
        return (
            instance.pair_selected[left, right]
            >= instance.selected[left] + instance.selected[right] - 1
        )

    def distance_limit_rule(instance, left, right):
        return (
            instance.min_distance
            + instance.big_constant * instance.pair_selected[left, right]
            <= instance.big_constant + instance.distance[left, right]
        )

    model.pair_left_limits = pyo.Constraint(model.pairs, rule=pair_left_rule)
    model.pair_right_limits = pyo.Constraint(model.pairs, rule=pair_right_rule)
    model.pair_lower_limits = pyo.Constraint(model.pairs, rule=pair_lower_rule)
    model.distance_limits = pyo.Constraint(model.pairs, rule=distance_limit_rule)

    model.objective = pyo.Objective(
        expr=model.min_distance,
        sense=pyo.maximize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi raises RuntimeError when no feasible solution can be loaded.
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}