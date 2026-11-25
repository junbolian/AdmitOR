# IR: {"sets":{"staff":[0,1,2,3,4],"registers":[0,1,2,3,4]},"params":{"cost_matrix":"5x5 assignment costs read from params['cost_matrix']"},"variables":{"assignment[i,j]":"Binary for each staff i and register j"},"constraints":["For every staff i: sum_j assignment[i,j] == 1","For every register j: sum_i assignment[i,j] == 1"],"objective":"Minimize sum_i sum_j cost_matrix[i][j] * assignment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.staff = pyo.RangeSet(0, 4)
    model.registers = pyo.RangeSet(0, 4)

    model.assignment_cost = pyo.Param(
        model.staff,
        model.registers,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.staff,
        model.registers,
        domain=pyo.Binary,
    )

    def staff_assignment_rule(mdl, i):
        return sum(mdl.assignment[i, j] for j in mdl.registers) == 1

    model.staff_assignment = pyo.Constraint(
        model.staff,
        rule=staff_assignment_rule,
    )

    def register_assignment_rule(mdl, j):
        return sum(mdl.assignment[i, j] for i in mdl.staff) == 1

    model.register_assignment = pyo.Constraint(
        model.registers,
        rule=register_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.assignment[i, j]
            for i in model.staff
            for j in model.registers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}