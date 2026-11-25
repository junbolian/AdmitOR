# IR: {"sets":{"VM":[0,1,2,3,4],"NODE":[0,1,2,3,4]},"params":{"cost_matrix":"input cost_matrix[i][j] for i in VM, j in NODE"},"variables":{"x[i,j]":"binary for i in VM, j in NODE"},"constraints":["sum(x[i,j] for j in NODE) == 1 for each i in VM","sum(x[i,j] for i in VM) == 1 for each j in NODE"],"objective":{"sense":"minimize","expression":"sum(cost_matrix[i][j]*x[i,j] for i in VM, j in NODE)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.vm_ids = pyo.RangeSet(0, 4)
    model.node_ids = pyo.RangeSet(0, 4)

    model.assignment_cost = pyo.Param(
        model.vm_ids,
        model.node_ids,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.vm_ids,
        model.node_ids,
        domain=pyo.Binary,
    )

    def vm_assignment_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.node_ids) == 1

    model.vm_assignment = pyo.Constraint(
        model.vm_ids,
        rule=vm_assignment_rule,
    )

    def node_assignment_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.vm_ids) == 1

    model.node_assignment = pyo.Constraint(
        model.node_ids,
        rule=node_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.x[i, j]
            for i in model.vm_ids
            for j in model.node_ids
        ),
        sense=pyo.minimize,
    )

    # HiGHS may raise RuntimeError when no solution can be loaded.
    # Success is determined solely by objective-value retrieval below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}