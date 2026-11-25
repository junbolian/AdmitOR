# IR: {"sets":{"N":["node_0","node_1","node_2","node_3","node_4"],"P":"unordered pairs of distinct nodes"},"params":{"num_facilities_selected":"required number of selected nodes","big_M":"pairwise relaxation constant","distances":"pairwise distance data, absent from the supplied specification"},"variables":{"selected[i]":"binary","pair_selected[i,j]":"binary","MinDistance":"nonnegative real"},"constraints":["sum(selected[i] for i in N) == num_facilities_selected","pair_selected[i,j] <= selected[i] for (i,j) in P","pair_selected[i,j] <= selected[j] for (i,j) in P","pair_selected[i,j] >= selected[i]+selected[j]-1 for (i,j) in P","MinDistance <= distances[i,j]+big_M*(1-pair_selected[i,j]) for (i,j) in P"],"objective":"maximize MinDistance"}
#
# The specification omits all ten numerical distances. Neither the selection
# count nor big_M determines them, so a numerical optimum cannot be recovered
# from the two listed parameters alone. Inventing distances would change the
# problem. This script solves the stated model if the missing data are supplied
# as params["distances"][(node_i, node_j)]; otherwise it reports missing data.

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    selection_count = params["num_facilities_selected"]
    big_m = params["big_M"]

    nodes = tuple(f"node_{idx}" for idx in range(5))
    pairs = tuple(combinations(nodes, 2))

    supplied_distances = params.get("distances")
    if supplied_distances is None:
        return {"objective": None, "status": "missing_distances"}

    distances = {}
    for first, second in pairs:
        if (first, second) in supplied_distances:
            distances[first, second] = supplied_distances[first, second]
        elif (second, first) in supplied_distances:
            distances[first, second] = supplied_distances[second, first]
        else:
            return {"objective": None, "status": "missing_distances"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.pairs = pyo.Set(initialize=pairs, dimen=2, ordered=True)

    model.selection_count = pyo.Param(initialize=selection_count)
    model.big_m = pyo.Param(initialize=big_m)
    model.distances = pyo.Param(model.pairs, initialize=distances)

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_selected = pyo.Var(model.pairs, domain=pyo.Binary)
    model.MinDistance = pyo.Var(domain=pyo.NonNegativeReals)

    model.selection_total = pyo.Constraint(
        expr=sum(model.selected[node] for node in model.nodes)
        == model.selection_count
    )

    def first_endpoint_rule(instance, first, second):
        return instance.pair_selected[first, second] <= instance.selected[first]

    def second_endpoint_rule(instance, first, second):
        return instance.pair_selected[first, second] <= instance.selected[second]

    def pair_lower_rule(instance, first, second):
        return instance.pair_selected[first, second] >= (
            instance.selected[first] + instance.selected[second] - 1
        )

    def distance_limit_rule(instance, first, second):
        return instance.MinDistance <= (
            instance.distances[first, second]
            + instance.big_m * (1 - instance.pair_selected[first, second])
        )

    model.first_endpoint_limit = pyo.Constraint(
        model.pairs, rule=first_endpoint_rule
    )
    model.second_endpoint_limit = pyo.Constraint(
        model.pairs, rule=second_endpoint_rule
    )
    model.pair_lower_limit = pyo.Constraint(
        model.pairs, rule=pair_lower_rule
    )
    model.distance_limit = pyo.Constraint(
        model.pairs, rule=distance_limit_rule
    )

    model.objective = pyo.Objective(
        expr=model.MinDistance, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}