# IR: {"sets":{"V":[0,1,2,3,4,5,6,7,8,9],"R":[0,1,2,3,4,5,6,7,8,9],"E":[[5,8],[4,9],[3,7],[0,3],[1,4],[2,3],[6,7],[4,5],[3,9],[5,9],[6,9]]},"params":{},"variables":{"x[v,r]":"Binary: variable v is assigned register r","y[r]":"Binary: register r is allocated"},"constraints":["For each v in V: sum(x[v,r] for r in R) = 1","For each (u,v) in E and r in R: x[u,r] + x[v,r] <= 1","For each v in V and r in R: x[v,r] <= y[r]"],"objective":"Minimize sum(y[r] for r in R)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize register usage for the specified interference graph."""
    # No numeric parameters are listed; all data below are structural.
    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=range(10), ordered=True)
    model.R = pyo.Set(initialize=range(10), ordered=True)
    model.E = pyo.Set(
        dimen=2,
        initialize=[
            (5, 8),
            (4, 9),
            (3, 7),
            (0, 3),
            (1, 4),
            (2, 3),
            (6, 7),
            (4, 5),
            (3, 9),
            (5, 9),
            (6, 9),
        ],
    )

    model.x = pyo.Var(model.V, model.R, domain=pyo.Binary)
    model.y = pyo.Var(model.R, domain=pyo.Binary)

    def assignment_rule(instance, vertex):
        return sum(instance.x[vertex, reg] for reg in instance.R) == 1

    model.assignment_constraints = pyo.Constraint(
        model.V, rule=assignment_rule
    )

    def interference_rule(instance, vertex_u, vertex_v, reg):
        return instance.x[vertex_u, reg] + instance.x[vertex_v, reg] <= 1

    model.interference_constraints = pyo.Constraint(
        model.E, model.R, rule=interference_rule
    )

    def allocation_rule(instance, vertex, reg):
        return instance.x[vertex, reg] <= instance.y[reg]

    model.allocation_constraints = pyo.Constraint(
        model.V, model.R, rule=allocation_rule
    )

    model.register_count = pyo.Objective(
        expr=sum(model.y[reg] for reg in model.R),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Preserve unexpected solver exceptions.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.register_count))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}