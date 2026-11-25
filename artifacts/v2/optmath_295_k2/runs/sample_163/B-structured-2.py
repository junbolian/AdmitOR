# IR: {"sets":{"N":[0,1,2,3,4],"A":"[(i,j) for i in N for j in N if i != j], row-major"},"params":{"pairwise_benefits":"params['pairwise_benefits']: 20 real weights indexed by A in order","num_selected":"params['num_selected']: exact cardinality"},"variables":{"selected[i]":"Binary, i in N","pair_active[i,j]":"Binary, (i,j) in A"},"constraints":["sum(selected[i] for i in N) == num_selected","pair_active[i,j] <= selected[i] for (i,j) in A","pair_active[i,j] <= selected[j] for (i,j) in A","pair_active[i,j] >= selected[i] + selected[j] - 1 for (i,j) in A"],"objective":"maximize sum(pairwise_benefits[i,j] * pair_active[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = range(5)
    ordered_pairs = [
        (i, j)
        for i in nodes
        for j in nodes
        if i != j
    ]

    benefits = list(params["pairwise_benefits"])
    num_selected = params["num_selected"]

    if len(benefits) != len(ordered_pairs):
        raise ValueError("pairwise_benefits must contain exactly 20 weights.")

    model = pyo.ConcreteModel()

    model.locations = pyo.Set(initialize=nodes, ordered=True)
    model.ordered_pairs = pyo.Set(
        dimen=2,
        initialize=ordered_pairs,
        ordered=True,
    )

    model.benefit_weight = pyo.Param(
        model.ordered_pairs,
        initialize=dict(zip(ordered_pairs, benefits)),
        within=pyo.Reals,
    )
    model.selection_count = pyo.Param(
        initialize=num_selected,
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.locations, domain=pyo.Binary)
    model.pair_active = pyo.Var(model.ordered_pairs, domain=pyo.Binary)

    model.cardinality_constraint = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.locations)
        == model.selection_count
    )

    def first_endpoint_rule(instance, i, j):
        return instance.pair_active[i, j] <= instance.selected[i]

    def second_endpoint_rule(instance, i, j):
        return instance.pair_active[i, j] <= instance.selected[j]

    def joint_activation_rule(instance, i, j):
        return (
            instance.pair_active[i, j]
            >= instance.selected[i] + instance.selected[j] - 1
        )

    model.first_endpoint_constraint = pyo.Constraint(
        model.ordered_pairs, rule=first_endpoint_rule
    )
    model.second_endpoint_constraint = pyo.Constraint(
        model.ordered_pairs, rule=second_endpoint_rule
    )
    model.joint_activation_constraint = pyo.Constraint(
        model.ordered_pairs, rule=joint_activation_rule
    )

    # Count every ordered interaction, as specified by the parameter definition.
    model.total_benefit = pyo.Objective(
        expr=sum(
            model.benefit_weight[i, j] * model.pair_active[i, j]
            for i, j in model.ordered_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_benefit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}