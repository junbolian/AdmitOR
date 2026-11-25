# IR: {"sets":{"N":[0,1,2,3,4],"A":"[(i,j) for i in N for j in N if i != j], row-major"},"params":{"pairwise_benefits":"20 ordered-pair weights from params['pairwise_benefits']","num_selected":"exact cardinality from params['num_selected']"},"variables":{"selected[i]":"binary, i in N","pair_active[i,j]":"binary, (i,j) in A"},"constraints":["sum(selected[i] for i in N) == num_selected","pair_active[i,j] <= selected[i] for (i,j) in A","pair_active[i,j] <= selected[j] for (i,j) in A","pair_active[i,j] >= selected[i] + selected[j] - 1 for (i,j) in A"],"objective":"maximize sum(pairwise_benefits[i,j] * pair_active[i,j] for (i,j) in A); count both ordered directions"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = range(5)
    ordered_pairs = [
        (i, j) for i in nodes for j in nodes if i != j
    ]
    benefits = list(params["pairwise_benefits"])
    required_count = params["num_selected"]

    if len(benefits) != len(ordered_pairs):
        return {"objective": None, "status": "invalid_benefit_count"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.ordered_pairs = pyo.Set(
        dimen=2, initialize=ordered_pairs, ordered=True
    )

    model.benefit = pyo.Param(
        model.ordered_pairs,
        initialize={
            pair: benefits[position]
            for position, pair in enumerate(ordered_pairs)
        },
        within=pyo.Reals,
    )
    model.required_count = pyo.Param(
        initialize=required_count, within=pyo.Reals
    )

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_active = pyo.Var(model.ordered_pairs, domain=pyo.Binary)

    model.selection_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.nodes)
        == model.required_count
    )

    def first_endpoint_rule(instance, i, j):
        return instance.pair_active[i, j] <= instance.selected[i]

    def second_endpoint_rule(instance, i, j):
        return instance.pair_active[i, j] <= instance.selected[j]

    def both_endpoints_rule(instance, i, j):
        return (
            instance.pair_active[i, j]
            >= instance.selected[i] + instance.selected[j] - 1
        )

    model.first_endpoint_limit = pyo.Constraint(
        model.ordered_pairs, rule=first_endpoint_rule
    )
    model.second_endpoint_limit = pyo.Constraint(
        model.ordered_pairs, rule=second_endpoint_rule
    )
    model.both_endpoints_activation = pyo.Constraint(
        model.ordered_pairs, rule=both_endpoints_rule
    )

    model.total_benefit = pyo.Objective(
        expr=sum(
            model.benefit[i, j] * model.pair_active[i, j]
            for i, j in model.ordered_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_benefit))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}