# IR: {"sets":{"N":[0,1,2,3,4],"A":"{(i,j) in N x N: i != j}"},"params":{"score[i,j]":"params[f'interaction_score_{i}_{j}'] for (i,j) in A"},"variables":{"selected[i]":"Binary for i in N","joint[i,j]":"Binary for (i,j) in A"},"constraints":["sum(selected[i] for i in N) == 2","joint[i,j] <= selected[i] for (i,j) in A","joint[i,j] <= selected[j] for (i,j) in A","joint[i,j] >= selected[i] + selected[j] - 1 for (i,j) in A"],"objective":{"sense":"maximize","expression":"sum(score[i,j] * joint[i,j] for (i,j) in A)","interpretation":"Count both directed interaction scores for the selected pair."}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ],
        ordered=True,
    )

    model.score = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"interaction_score_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.nodes, domain=pyo.Binary)
    model.joint = pyo.Var(model.arcs, domain=pyo.Binary)

    model.facility_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.nodes) == 2
    )

    def first_endpoint_rule(instance, i, j):
        return instance.joint[i, j] <= instance.selected[i]

    def second_endpoint_rule(instance, i, j):
        return instance.joint[i, j] <= instance.selected[j]

    def joint_lower_bound_rule(instance, i, j):
        return (
            instance.joint[i, j]
            >= instance.selected[i] + instance.selected[j] - 1
        )

    model.first_endpoint = pyo.Constraint(
        model.arcs, rule=first_endpoint_rule
    )
    model.second_endpoint = pyo.Constraint(
        model.arcs, rule=second_endpoint_rule
    )
    model.joint_lower_bound = pyo.Constraint(
        model.arcs, rule=joint_lower_bound_rule
    )

    model.total_benefit = pyo.Objective(
        expr=sum(
            model.score[i, j] * model.joint[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_benefit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}