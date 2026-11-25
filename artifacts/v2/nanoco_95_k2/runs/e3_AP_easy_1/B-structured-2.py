# IR: {"sets":{"VM":[0,1,2,3,4],"SERVER":[0,1,2,3,4]},"params":{"cost_matrix":"5x5 assignment costs read from params['cost_matrix']"},"variables":{"assignment[VM,SERVER]":"Binary"},"constraints":["For each VM i: sum(assignment[i,j] for j in SERVER) == 1","For each SERVER j: sum(assignment[i,j] for i in VM) == 1"],"objective":"Minimize sum(cost_matrix[i][j] * assignment[i,j] for i in VM for j in SERVER)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.vm_set = pyo.RangeSet(0, 4)
    model.server_set = pyo.RangeSet(0, 4)

    model.assignment_cost = pyo.Param(
        model.vm_set,
        model.server_set,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.vm_set,
        model.server_set,
        domain=pyo.Binary,
    )

    def vm_assignment_rule(mdl, i):
        return sum(
            mdl.assignment[i, j] for j in mdl.server_set
        ) == 1

    model.vm_assignment_constraint = pyo.Constraint(
        model.vm_set,
        rule=vm_assignment_rule,
    )

    def server_assignment_rule(mdl, j):
        return sum(
            mdl.assignment[i, j] for i in mdl.vm_set
        ) == 1

    model.server_assignment_constraint = pyo.Constraint(
        model.server_set,
        rule=server_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.assignment[i, j]
            for i in model.vm_set
            for j in model.server_set
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}