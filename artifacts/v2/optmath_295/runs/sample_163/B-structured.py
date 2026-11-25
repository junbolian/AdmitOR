# IR: {"sets":{"N":[0,1,2,3,4],"A":"{(i,j) in N x N: i != j}"},"params":{"coverage_benefit_ij":"params['coverage_benefit_' + str(i) + str(j)] for (i,j) in A","num_centers_to_select":"params['num_centers_to_select']"},"variables":{"selected[i]":"binary for i in N","pair_active[i,j]":"binary for (i,j) in A"},"constraints":["sum(selected[i] for i in N) == num_centers_to_select","pair_active[i,j] <= selected[i] for (i,j) in A","pair_active[i,j] <= selected[j] for (i,j) in A","pair_active[i,j] >= selected[i] + selected[j] - 1 for (i,j) in A"],"objective":"maximize sum(coverage_benefit_ij * pair_active[i,j] for (i,j) in A); count both supplied directions"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(5)
            for destination in range(5)
            if origin != destination
        ],
        ordered=True,
    )

    model.coverage_benefit = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[
                f"coverage_benefit_{origin}{destination}"
            ]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )
    model.required_centers = pyo.Param(
        initialize=params["num_centers_to_select"],
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_active = pyo.Var(model.arcs, domain=pyo.Binary)

    model.selection_count = pyo.Constraint(
        expr=sum(model.selected[node] for node in model.nodes)
        == model.required_centers
    )

    def origin_activation_rule(instance, origin, destination):
        return instance.pair_active[origin, destination] <= instance.selected[origin]

    def destination_activation_rule(instance, origin, destination):
        return (
            instance.pair_active[origin, destination]
            <= instance.selected[destination]
        )

    def joint_activation_rule(instance, origin, destination):
        return (
            instance.pair_active[origin, destination]
            >= instance.selected[origin] + instance.selected[destination] - 1
        )

    model.origin_activation = pyo.Constraint(
        model.arcs, rule=origin_activation_rule
    )
    model.destination_activation = pyo.Constraint(
        model.arcs, rule=destination_activation_rule
    )
    model.joint_activation = pyo.Constraint(
        model.arcs, rule=joint_activation_rule
    )

    model.total_coverage = pyo.Objective(
        expr=sum(
            model.coverage_benefit[origin, destination]
            * model.pair_active[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_coverage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}