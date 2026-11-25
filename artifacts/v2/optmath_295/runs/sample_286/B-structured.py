# IR: {"sets":{"N":"node_i for i in range(params['num_nodes'])","P":"unordered pairs of distinct nodes in N"},"params":{"num_nodes":"required","min_distance_lower_bound":"required","min_distance_upper_bound":"required","big_M":"required","exact_selection_count":"required","distances":"missing from the supplied specification; mapping (node_i,node_j) to distance is necessary for every pair"},"variables":{"selected[N]":"binary","pair_selected[P]":"binary","MinDistance":"real in [min_distance_lower_bound,min_distance_upper_bound]"},"constraints":["sum(selected[i] for i in N) = exact_selection_count","MinDistance <= distances[i,j] + big_M*(1-pair_selected[i,j]) for (i,j) in P","pair_selected[i,j] <= selected[i] for (i,j) in P","pair_selected[i,j] <= selected[j] for (i,j) in P","pair_selected[i,j] >= selected[i]+selected[j]-1 for (i,j) in P"],"objective":"maximize MinDistance","failure_handling":"return missing_distances if necessary distance data are absent; otherwise attempt HiGHS and determine success solely by objective retrieval"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # The five listed parameters do not specify any pairwise distances.
    # Node labels alone do not define distances, and the statement supplies
    # neither numerical distance constraints nor coordinates nor a formula.
    # Consequently, no mathematically justified correction can produce a
    # numerical optimum using only those five parameters. This implementation
    # solves the stated model when the missing distances are supplied through
    # params["distances"]; otherwise it reports the missing data.
    # Example key format: ("node_0", "node_1"). Values must be actual input data.

    num_nodes = params["num_nodes"]
    lower_bound = params["min_distance_lower_bound"]
    upper_bound = params["min_distance_upper_bound"]
    big_M = params["big_M"]
    selection_count = params["exact_selection_count"]

    nodes = [f"node_{idx}" for idx in range(num_nodes)]
    pairs = [
        (nodes[first_idx], nodes[second_idx])
        for first_idx in range(num_nodes)
        for second_idx in range(first_idx + 1, num_nodes)
    ]

    pair_distances = {}
    if pairs:
        if "distances" not in params:
            return {"objective": None, "status": "missing_distances"}

        supplied_distances = params["distances"]
        for first_node, second_node in pairs:
            if (first_node, second_node) in supplied_distances:
                distance = supplied_distances[first_node, second_node]
            elif (second_node, first_node) in supplied_distances:
                distance = supplied_distances[second_node, first_node]
            else:
                return {"objective": None, "status": "missing_distances"}

            if distance is None:
                return {"objective": None, "status": "missing_distances"}

            pair_distances[first_node, second_node] = distance

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.pairs = pyo.Set(initialize=pairs, dimen=2, ordered=True)

    model.distance_lower_bound = pyo.Param(initialize=lower_bound)
    model.distance_upper_bound = pyo.Param(initialize=upper_bound)
    model.relaxation_constant = pyo.Param(initialize=big_M)
    model.required_selection_count = pyo.Param(initialize=selection_count)
    model.pair_distance = pyo.Param(
        model.pairs,
        initialize=pair_distances,
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_selected = pyo.Var(model.pairs, domain=pyo.Binary)
    model.MinDistance = pyo.Var(
        domain=pyo.Reals,
        bounds=(model.distance_lower_bound, model.distance_upper_bound),
    )

    model.selection_count_constraint = pyo.Constraint(
        expr=(
            model.required_selection_count,
            sum(model.selected[node] for node in model.nodes),
            model.required_selection_count,
        )
    )

    def distance_limit_rule(instance, first_node, second_node):
        return instance.MinDistance <= (
            instance.pair_distance[first_node, second_node]
            + instance.relaxation_constant
            * (1 - instance.pair_selected[first_node, second_node])
        )

    model.distance_limit_constraints = pyo.Constraint(
        model.pairs, rule=distance_limit_rule
    )

    def pair_first_upper_rule(instance, first_node, second_node):
        return (
            instance.pair_selected[first_node, second_node]
            <= instance.selected[first_node]
        )

    model.pair_first_upper_constraints = pyo.Constraint(
        model.pairs, rule=pair_first_upper_rule
    )

    def pair_second_upper_rule(instance, first_node, second_node):
        return (
            instance.pair_selected[first_node, second_node]
            <= instance.selected[second_node]
        )

    model.pair_second_upper_constraints = pyo.Constraint(
        model.pairs, rule=pair_second_upper_rule
    )

    def pair_lower_rule(instance, first_node, second_node):
        return instance.pair_selected[first_node, second_node] >= (
            instance.selected[first_node]
            + instance.selected[second_node]
            - 1
        )

    model.pair_lower_constraints = pyo.Constraint(
        model.pairs, rule=pair_lower_rule
    )

    model.objective = pyo.Objective(
        expr=model.MinDistance,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}