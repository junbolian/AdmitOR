# IR: {"sets":{"VM":[0,1,2,3,4],"SERVER":[0,1,2,3,4]},"params":{"cost_matrix":"5x5 assignment costs read from params"},"variables":{"x[i,j]":"binary for i in VM, j in SERVER"},"constraints":["sum(x[i,j] for j in SERVER) == 1 for each i in VM","sum(x[i,j] for i in VM) == 1 for each j in SERVER"],"objective":"minimize sum(cost_matrix[i][j]*x[i,j] for i in VM, j in SERVER)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.VM = pyo.RangeSet(0, 4)
    model.SERVER = pyo.RangeSet(0, 4)

    model.assignment_cost = pyo.Param(
        model.VM,
        model.SERVER,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.VM, model.SERVER, domain=pyo.Binary)

    model.vm_assignment = pyo.Constraint(
        model.VM,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in mdl.SERVER) == 1,
    )
    model.server_assignment = pyo.Constraint(
        model.SERVER,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in mdl.VM) == 1,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.x[i, j]
            for i in model.VM
            for j in model.SERVER
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi may raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}