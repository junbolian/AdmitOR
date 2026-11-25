# IR: {"sets":{"N":[0,1,2,3,4],"A":"[(i,j) for i in N for j in N if i != j]"},"params":{"weights":"params['weights']; 20 real weights mapped to A in lexicographic order"},"variables":{"selected[i]":"binary for i in N","pair_selected[i,j]":"binary for (i,j) in A"},"constraints":["sum(selected[i] for i in N) == 3","pair_selected[i,j] <= selected[i] for (i,j) in A","pair_selected[i,j] <= selected[j] for (i,j) in A","pair_selected[i,j] >= selected[i] + selected[j] - 1 for (i,j) in A"],"objective":"maximize sum(weights[i,j] * pair_selected[i,j] for (i,j) in A); count both directed weights for each selected pair"}
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

    supplied_weights = params["weights"]
    if len(supplied_weights) != len(ordered_pairs):
        raise ValueError("params['weights'] must contain exactly 20 values.")

    weight_map = dict(zip(ordered_pairs, supplied_weights))

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.ordered_pairs = pyo.Set(
        initialize=ordered_pairs, dimen=2, ordered=True
    )
    model.dispersion_weights = pyo.Param(
        model.ordered_pairs,
        initialize=weight_map,
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_selected = pyo.Var(
        model.ordered_pairs, domain=pyo.Binary
    )

    model.facility_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.nodes) == 3
    )

    def first_endpoint_rule(block, i, j):
        return block.pair_selected[i, j] <= block.selected[i]

    def second_endpoint_rule(block, i, j):
        return block.pair_selected[i, j] <= block.selected[j]

    def both_endpoints_rule(block, i, j):
        return (
            block.pair_selected[i, j]
            >= block.selected[i] + block.selected[j] - 1
        )

    model.first_endpoint_link = pyo.Constraint(
        model.ordered_pairs, rule=first_endpoint_rule
    )
    model.second_endpoint_link = pyo.Constraint(
        model.ordered_pairs, rule=second_endpoint_rule
    )
    model.both_endpoints_link = pyo.Constraint(
        model.ordered_pairs, rule=both_endpoints_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.dispersion_weights[i, j] * model.pair_selected[i, j]
            for i, j in model.ordered_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Leave objective retrieval as the sole success test.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective_value"}

    return {"objective": obj_val, "status": "optimal"}