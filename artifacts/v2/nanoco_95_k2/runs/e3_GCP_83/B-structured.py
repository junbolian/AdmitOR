# IR: {"sets":{"V":[0,1,2,3,4,5,6,7,8,9],"R":[0,1,2,3,4,5,6,7,8,9],"E":[[5,8],[4,9],[3,7],[0,3],[1,4],[2,3],[6,7],[4,5],[3,9],[5,9],[6,9]]},"params":{},"variables":{"x[v,r]":"binary; variable v uses register r","y[r]":"binary; register r is allocated"},"constraints":["sum(x[v,r] for r in R) == 1 for v in V","x[u,r] + x[v,r] <= 1 for (u,v) in E, r in R","x[v,r] <= y[r] for v in V, r in R"],"objective":"minimize sum(y[r] for r in R)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize the number of registers for the fixed interference graph."""
    model = pyo.ConcreteModel()

    model.V = pyo.RangeSet(0, 9)
    model.R = pyo.RangeSet(0, 9)
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

    def assignment_rule(model, variable):
        return sum(model.x[variable, register] for register in model.R) == 1

    model.assignment_constraints = pyo.Constraint(
        model.V, rule=assignment_rule
    )

    def interference_rule(model, first, second, register):
        return model.x[first, register] + model.x[second, register] <= 1

    model.interference_constraints = pyo.Constraint(
        model.E, model.R, rule=interference_rule
    )

    def allocation_rule(model, variable, register):
        return model.x[variable, register] <= model.y[register]

    model.allocation_constraints = pyo.Constraint(
        model.V, model.R, rule=allocation_rule
    )

    model.register_count = pyo.Objective(
        expr=sum(model.y[register] for register in model.R),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.register_count))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}