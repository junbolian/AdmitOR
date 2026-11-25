# IR: {"sets":{"developers":[0,1,2,3,4],"modules":[0,1,2,3,4]},"params":{"cost_matrix":"input 5x5 real matrix indexed by developer,module"},"variables":{"assignment[developer,module]":"binary"},"constraints":["For each developer: sum(assignment[developer,module] for module in modules) = 1","For each module: sum(assignment[developer,module] for developer in developers) = 1"],"objective":"minimize sum(cost_matrix[developer][module] * assignment[developer,module] for developer in developers for module in modules)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.developers = pyo.RangeSet(0, 4)
    model.modules = pyo.RangeSet(0, 4)

    model.effort_cost = pyo.Param(
        model.developers,
        model.modules,
        initialize={
            (developer, module): cost_matrix[developer][module]
            for developer in model.developers
            for module in model.modules
        },
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.developers, model.modules, domain=pyo.Binary
    )

    def developer_assignment_rule(instance, developer):
        return sum(
            instance.assignment[developer, module]
            for module in instance.modules
        ) == 1

    model.developer_assignment = pyo.Constraint(
        model.developers, rule=developer_assignment_rule
    )

    def module_assignment_rule(instance, module):
        return sum(
            instance.assignment[developer, module]
            for developer in instance.developers
        ) == 1

    model.module_assignment = pyo.Constraint(
        model.modules, rule=module_assignment_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.effort_cost[developer, module]
            * model.assignment[developer, module]
            for developer in model.developers
            for module in model.modules
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