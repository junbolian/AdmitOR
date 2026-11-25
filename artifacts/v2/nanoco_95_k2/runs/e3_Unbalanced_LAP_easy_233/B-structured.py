# IR: {"sets":{"attorneys":"0..7","documents":"0..3"},"params":{"cost":"real[attorneys,documents], read from params['cost']"},"variables":{"assignment":"binary[attorneys,documents]"},"constraints":["For each document j: sum_i assignment[i,j] = 1","For each attorney i: sum_j assignment[i,j] <= 1"],"objective":"Minimize sum_i sum_j cost[i,j] * assignment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.attorneys = pyo.RangeSet(0, 7)
    model.documents = pyo.RangeSet(0, 3)

    model.cost = pyo.Param(
        model.attorneys,
        model.documents,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.attorneys,
        model.documents,
        domain=pyo.Binary,
    )

    def document_assignment_rule(mdl, j):
        return sum(
            mdl.assignment[i, j] for i in mdl.attorneys
        ) == 1

    model.document_assignment = pyo.Constraint(
        model.documents,
        rule=document_assignment_rule,
    )

    def attorney_capacity_rule(mdl, i):
        return sum(
            mdl.assignment[i, j] for j in mdl.documents
        ) <= 1

    model.attorney_capacity = pyo.Constraint(
        model.attorneys,
        rule=attorney_capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.assignment[i, j]
            for i in model.attorneys
            for j in model.documents
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}