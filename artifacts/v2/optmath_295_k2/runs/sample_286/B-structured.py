# IR: {"sets":{"N":["node_0","node_1","node_2","node_3","node_4"],"P":"unordered pairs of distinct nodes in N"},"params":{"num_facilities_selected":"params['num_facilities_selected']","big_M":"params['big_M']","distance":"params['distances'], keyed by node pairs; required but not supplied in the problem"},"variables":{"selected[i]":"Binary","pair_selected[i,j]":"Binary","MinDistance":"NonNegativeReals"},"constraints":["sum(selected[i] for i in N) == num_facilities_selected","MinDistance <= distance[i,j] + big_M*(1-pair_selected[i,j]) for (i,j) in P","pair_selected[i,j] <= selected[i] for (i,j) in P","pair_selected[i,j] <= selected[j] for (i,j) in P","pair_selected[i,j] >= selected[i]+selected[j]-1 for (i,j) in P"],"objective":"maximize MinDistance"}
#
# The statement supplies neither distances nor numerical pairwise constraints.
# Node labels alone do not determine distances. Consequently, no numerical
# optimum can be computed from the two listed parameters alone. This script
# solves the stated model if the missing distance mapping is supplied; otherwise
# it returns an explicit failure rather than inventing distances.

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities_selected = params["num_facilities_selected"]
    big_M = params["big_M"]

    nodes = tuple(f"node_{idx}" for idx in range(5))
    pairs = tuple(combinations(nodes, 2))

    if "distances" not in params:
        return {"objective": None, "status": "missing_distance_data"}

    supplied_distances = params["distances"]
    distances = {}
    for first, second in pairs:
        if (first, second) in supplied_distances:
            distances[first, second] = supplied_distances[first, second]
        elif (second, first) in supplied_distances:
            distances[first, second] = supplied_distances[second, first]
        else:
            return {"objective": None, "status": "incomplete_distance_data"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.pairs = pyo.Set(initialize=pairs, dimen=2, ordered=True)

    model.facility_count = pyo.Param(initialize=num_facilities_selected)
    model.relaxation_constant = pyo.Param(initialize=big_M)
    model.distance = pyo.Param(model.pairs, initialize=distances)

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_selected = pyo.Var(model.pairs, domain=pyo.Binary)
    model.MinDistance = pyo.Var(domain=pyo.NonNegativeReals)

    model.selection_count = pyo.Constraint(
        expr=sum(model.selected[node] for node in model.nodes)
        == model.facility_count
    )

    def distance_limit_rule(instance, first, second):
        return instance.MinDistance <= (
            instance.distance[first, second]
            + instance.relaxation_constant
            * (1 - instance.pair_selected[first, second])
        )

    def pair_first_rule(instance, first, second):
        return instance.pair_selected[first, second] <= instance.selected[first]

    def pair_second_rule(instance, first, second):
        return instance.pair_selected[first, second] <= instance.selected[second]

    def pair_lower_rule(instance, first, second):
        return instance.pair_selected[first, second] >= (
            instance.selected[first] + instance.selected[second] - 1
        )

    model.distance_limits = pyo.Constraint(model.pairs, rule=distance_limit_rule)
    model.pair_first_limits = pyo.Constraint(model.pairs, rule=pair_first_rule)
    model.pair_second_limits = pyo.Constraint(model.pairs, rule=pair_second_rule)
    model.pair_lower_limits = pyo.Constraint(model.pairs, rule=pair_lower_rule)

    model.objective = pyo.Objective(
        expr=model.MinDistance,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve can raise when HiGHS attempts to load a solution.
        # Success is still determined solely by objective-value retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}