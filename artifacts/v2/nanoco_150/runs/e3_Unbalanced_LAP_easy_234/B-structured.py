# IR: {"sets":{"developers":[0,1,2,3,4,5],"bugs":[0,1,2,3,4,5]},"params":{"assignment_cost":"real matrix supplied by params['assignment_cost'], indexed [developer][bug]"},"variables":{"assigned[developer,bug]":"binary"},"constraints":["For each developer: sum(assigned[developer,bug] for bug in bugs) == 1","For each bug: sum(assigned[developer,bug] for developer in developers) == 1"],"objective":"Minimize sum(assignment_cost[developer,bug] * assigned[developer,bug] for developer in developers for bug in bugs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_cost = params["assignment_cost"]

    model = pyo.ConcreteModel()
    model.developers = pyo.RangeSet(0, 5)
    model.bugs = pyo.RangeSet(0, 5)

    model.assignment_cost = pyo.Param(
        model.developers,
        model.bugs,
        initialize=lambda model, developer, bug: assignment_cost[developer][bug],
        within=pyo.Reals,
    )

    model.assigned = pyo.Var(
        model.developers,
        model.bugs,
        domain=pyo.Binary,
    )

    def developer_assignment_rule(model, developer):
        return sum(
            model.assigned[developer, bug] for bug in model.bugs
        ) == 1

    model.developer_assignment = pyo.Constraint(
        model.developers,
        rule=developer_assignment_rule,
    )

    def bug_assignment_rule(model, bug):
        return sum(
            model.assigned[developer, bug] for developer in model.developers
        ) == 1

    model.bug_assignment = pyo.Constraint(
        model.bugs,
        rule=bug_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[developer, bug]
            * model.assigned[developer, bug]
            for developer in model.developers
            for bug in model.bugs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}